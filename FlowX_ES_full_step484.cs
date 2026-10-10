#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.DrawingTools;
using NinjaTrader.NinjaScript.Indicators;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
	/// <summary>
	/// FlowXAbsorptionReversal_ES: Calibrated for S&P 500 (ES) Market Microstructure.
	/// Explores thick-book iceberg limit absorption at VWAP ±2.0σ extreme bands.
	/// Features:
	/// 1. Heavy-book sweep aggregation (250+ contracts on ES).
	/// 2. Structural wick stop loss (3.0 to 6.0 points = $150 to $300 risk).
	/// 3. Mean-reversion rotation targets (TP1 at ±1.0σ, TP2 at VWAP Midline).
	/// 4. Micro-Breakeven at +3.5 points (+$175 open profit).
	/// </summary>
	public class FlowXAbsorptionReversal_ES : Strategy
	{
		#region Private Fields - Session VWAP
		private double cumVolume;
		private double cumPV;
		private double cumPV2;
		private double currentVwap;
		private double currentStdDev;
		private double upperBand1;
		private double upperBand2;
		private double lowerBand1;
		private double lowerBand2;
		private DateTime currentTradingDay = DateTime.MinValue;
		private SessionIterator sessionIterator;
		#endregion

		#region Private Fields - Order Flow & BigTrade Sweeps
		private double lastBarVolume;
		private double lastTradePrice;
		private bool lastTradeWasBuy = true;

		// Contiguous Sweep Buffer
		private long currentSweepVol;
		private bool currentSweepIsBuy;
		private int lastBigBuyBar = -100;
		private int lastBigSellBar = -100;
		#endregion

		#region Private Fields - CVD & Delta
		private double sessionCvd;
		private double barOpenCvd;
		private double currBarDelta;
		#endregion

		#region Private Fields - Execution & Position Management
		private int lastEntryBar = -100;
		private int lastExitBar = -100;
		private bool tp1Filled;
		private bool isBreakevenArmed;
		private double currentPositionEntryPrice;
		private int sessionLossCount;
		private int lastKnownTradeCount;
		#endregion

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description							= "FlowX Absorption Reversal: Calibrated for S&P 500 (ES) Deep Liquidity.";
				Name								= "FlowXAbsorptionReversal_ES";
				Calculate							= Calculate.OnEachTick;
				EntriesPerDirection					= 1;
				EntryHandling						= EntryHandling.AllEntries;
				IsExitOnSessionCloseStrategy		= true;
				ExitOnSessionCloseSeconds			= 60;
				IsFillLimitOnTouch					= false;
				MaximumBarsLookBack					= MaximumBarsLookBack.TwoHundredFiftySix;
				OrderFillResolution					= OrderFillResolution.Standard;
				Slippage							= 1; // 1 tick slippage (0.25 on ES = $12.50)
				IncludeCommission					= true;

				// 1. Order Flow Parameters (Calibrated for ES)
				MinBigTradeSize						= 250;  // 250+ contracts institutional sweep threshold on ES

				// 2. VWAP Parameters
				VwapDev2							= 2.0;  // 2.0σ Extreme reversal zone

				// 3. Risk & Structural Execution (ES Scale: $50/pt)
				MinStopPoints						= 3.5;  // Minimum stop distance (14 ticks = $175/contract)
				MaxStopPoints						= 6.0;  // Maximum structural stop distance (24 ticks = $300/contract)
				Quantity							= 2;    // 2 contracts
				MaxLossesPerDay						= 2;    // Max losses per session

				// 4. Profit Harvesting
				BreakevenTriggerPoints				= 3.5;  // Profit points to lock in Breakeven (+14 ticks = $175/contract)

				// 5. Filters
				CooldownBars						= 3;    // Cooldown after an exit
				RequireCvdDivergence				= true; // Prevent fighting expanding delta
			}
			else if (State == State.Configure)
			{
				AddPlot(new Stroke(Brushes.Goldenrod, 2), PlotStyle.Line, "VWAP_Mean");
				AddPlot(new Stroke(Brushes.SlateGray, DashStyleHelper.Dash, 1), PlotStyle.Line, "Upper_2Sigma");
				AddPlot(new Stroke(Brushes.SlateGray, DashStyleHelper.Dash, 1), PlotStyle.Line, "Lower_2Sigma");
			}
			else if (State == State.DataLoaded)
			{
				sessionIterator = new SessionIterator(Bars);
				ClearSessionState();

				// Default broker stop (updated per entry wick)
				SetStopLoss(CalculationMode.Ticks, (int)Math.Round(MinStopPoints * 4));
			}
			else if (State == State.Terminated)
			{
				DumpBacktestResults();
			}
		}

		private void ClearSessionState()
		{
			cumVolume					= 0;
			cumPV						= 0;
			cumPV2						= 0;
			currentVwap					= 0;
			currentStdDev				= 0;
			upperBand1					= 0;
			upperBand2					= 0;
			lowerBand1					= 0;
			lowerBand2					= 0;
			sessionCvd					= 0;
			barOpenCvd					= 0;
			currBarDelta				= 0;
			lastBarVolume				= 0;
			currentSweepVol				= 0;
			lastBigBuyBar				= -100;
			lastBigSellBar				= -100;
			tp1Filled					= false;
			isBreakevenArmed			= false;
			sessionLossCount			= 0;
			currentPositionEntryPrice	= 0;
		}

		protected override void OnBarUpdate()
		{
			if (CurrentBar < 15)
				return;

			// --- 1. Session Detection & Daily Reset ---
			if (sessionIterator == null)
				sessionIterator = new SessionIterator(Bars);

			DateTime barDay = sessionIterator.GetTradingDay(Time[0]);
			if (barDay != currentTradingDay)
			{
				currentTradingDay = barDay;
				ClearSessionState();
			}

			// --- 2. Track Realized Trades for Session Loss Governor ---
			if (SystemPerformance.AllTrades.Count > lastKnownTradeCount)
			{
				for (int i = lastKnownTradeCount; i < SystemPerformance.AllTrades.Count; i++)
				{
					Trade t = SystemPerformance.AllTrades[i];
					if (t.ProfitCurrency < -5)
					{
						sessionLossCount++;
					}
				}
				lastKnownTradeCount = SystemPerformance.AllTrades.Count;
			}

			// --- 3. End-of-Day Mandatory Flatten ---
			DateTime sessionEnd = sessionIterator.GetTradingDayEndLocal(Time[0]);
			double minutesToSessionEnd = (sessionEnd - Time[0]).TotalMinutes;

			if (minutesToSessionEnd <= 2 && minutesToSessionEnd >= 0)
			{
				if (Position.MarketPosition != MarketPosition.Flat)
				{
					if (Position.MarketPosition == MarketPosition.Short)
						ExitShort("EOD_Exit");
					else
						ExitLong("EOD_Exit");

					lastExitBar = CurrentBar;
				}
				return;
			}

			// --- 4. Tick Order Flow Calculation ---
			double currentTickVolume = 0;
			if (IsFirstTickOfBar)
			{
				currentTickVolume = Volume[0];
				lastBarVolume     = Volume[0];
				barOpenCvd        = sessionCvd;
			}
			else
			{
				currentTickVolume = Volume[0] - lastBarVolume;
				if (currentTickVolume < 0) currentTickVolume = 0;
				lastBarVolume     = Volume[0];
			}

			if (currentTickVolume <= 0)
				currentTickVolume = 1;

			// Aggressor Classification (Tick Rule)
			double curAsk = GetCurrentAsk();
			double curBid = GetCurrentBid();
			bool isBuy    = lastTradeWasBuy;

			if (curAsk > 0 && curBid > 0)
			{
				if (Close[0] >= curAsk)
					isBuy = true;
				else if (Close[0] <= curBid)
					isBuy = false;
				else if (Close[0] > lastTradePrice)
					isBuy = true;
				else if (Close[0] < lastTradePrice)
					isBuy = false;
			}
			else
			{
				if (Close[0] > lastTradePrice)
					isBuy = true;
				else if (Close[0] < lastTradePrice)
					isBuy = false;
			}

			lastTradePrice  = Close[0];
			lastTradeWasBuy = isBuy;

			// CVD Accumulation
			double delta = isBuy ? currentTickVolume : -currentTickVolume;
			sessionCvd  += delta;
			currBarDelta = sessionCvd - barOpenCvd;

			// Contiguous Sweep Aggregation
			if (currentSweepIsBuy == isBuy)
			{
				currentSweepVol += (long)currentTickVolume;
			}
			else
			{
				currentSweepVol   = (long)currentTickVolume;
				currentSweepIsBuy  = isBuy;
			}

			if (currentTickVolume >= MinBigTradeSize || currentSweepVol >= MinBigTradeSize)
			{
				if (isBuy)
					lastBigBuyBar = CurrentBar;
				else
					lastBigSellBar = CurrentBar;
			}

			// --- 5. Closed-Form FlowX Session VWAP Math ---
			cumVolume += currentTickVolume;
			cumPV     += currentTickVolume * Close[0];
			cumPV2    += currentTickVolume * Close[0] * Close[0];

			if (cumVolume > 0)
			{
				currentVwap = cumPV / cumVolume;
				double variance = (cumPV2 / cumVolume) - (currentVwap * currentVwap);
				currentStdDev = Math.Sqrt(Math.Max(0, variance));

				upperBand1 = currentVwap + (1.0 * currentStdDev);
				upperBand2 = currentVwap + (VwapDev2 * currentStdDev);
				lowerBand1 = currentVwap - (1.0 * currentStdDev);
				lowerBand2 = currentVwap - (VwapDev2 * currentStdDev);

				Values[0][0] = currentVwap;
				Values[1][0] = upperBand2;
				Values[2][0] = lowerBand2;
			}

			// --- 6. Position & Target Management ---
			ManageDynamicTargets();

			// --- 7. Signal Execution ---
			if (Position.MarketPosition == MarketPosition.Flat)
			{
				if (sessionLossCount >= MaxLossesPerDay)
					return;

				if (CurrentBar == lastEntryBar || CurrentBar <= lastExitBar + CooldownBars)
					return;

				DateTime sessionBegin = sessionIterator.GetTradingDayBeginLocal(Time[0]);
				double minutesFromOpen = (Time[0] - sessionBegin).TotalMinutes;

				// Skip first 15 mins and last 30 mins
				if (minutesFromOpen < 15 || minutesToSessionEnd < 30)
					return;

				CheckForESEntries();
			}
		}

		private void CheckForESEntries()
		{
			if (currentVwap <= 0 || upperBand2 <= 0 || lowerBand2 <= 0)
				return;

			// ==========================================
			// SHORT SETUP: Bearish Absorption at +2.0σ
			// ==========================================
			bool testedUpperBand = (High[0] >= upperBand2 || High[1] >= upperBand2);
			bool buyersTrapped   = (CurrentBar - lastBigBuyBar <= 2);

			double upperWick     = High[0] - Math.Max(Open[0], Close[0]);
			bool hasUpperWick    = (upperWick >= 0.50); // 2 ticks wick on ES
			bool isBearishBar    = (Close[0] < Open[0]) && (Close[0] < High[0] - 0.50);
			bool cvdExhaustedShort = !RequireCvdDivergence || (currBarDelta <= (MinBigTradeSize * 0.4));

			if (testedUpperBand && buyersTrapped && hasUpperWick && isBearishBar && cvdExhaustedShort)
			{
				double entryPrice = Close[0];
				double trapWickHigh = Math.Max(High[0], High[1]) + (2 * TickSize);
				double stopPoints   = trapWickHigh - entryPrice;

				if (stopPoints >= 2.0 && stopPoints <= MaxStopPoints)
				{
					int stopTicks = (int)Math.Max(Math.Round(MinStopPoints * 4), Math.Round(stopPoints * 4));
					SetStopLoss(CalculationMode.Ticks, stopTicks);

					lastEntryBar              = CurrentBar;
					tp1Filled                 = false;
					isBreakevenArmed          = false;
					currentPositionEntryPrice = entryPrice;

					EnterShort(Quantity, "Short_Absorption");
					return;
				}
			}

			// ==========================================
			// LONG SETUP: Bullish Absorption at -2.0σ
			// ==========================================
			bool testedLowerBand = (Low[0] <= lowerBand2 || Low[1] <= lowerBand2);
			bool sellersTrapped  = (CurrentBar - lastBigSellBar <= 2);

			double lowerWick     = Math.Min(Open[0], Close[0]) - Low[0];
			bool hasLowerWick    = (lowerWick >= 0.50); // 2 ticks wick on ES
			bool isBullishBar    = (Close[0] > Open[0]) && (Close[0] > Low[0] + 0.50);
			bool cvdExhaustedLong = !RequireCvdDivergence || (currBarDelta >= -(MinBigTradeSize * 0.4));

			if (testedLowerBand && sellersTrapped && hasLowerWick && isBullishBar && cvdExhaustedLong)
			{
				double entryPrice = Close[0];
				double trapWickLow = Math.Min(Low[0], Low[1]) - (2 * TickSize);
				double stopPoints  = entryPrice - trapWickLow;

				if (stopPoints >= 2.0 && stopPoints <= MaxStopPoints)
				{
					int stopTicks = (int)Math.Max(Math.Round(MinStopPoints * 4), Math.Round(stopPoints * 4));
					SetStopLoss(CalculationMode.Ticks, stopTicks);

					lastEntryBar              = CurrentBar;
					tp1Filled                 = false;
					isBreakevenArmed          = false;
					currentPositionEntryPrice = entryPrice;

					EnterLong(Quantity, "Long_Absorption");
					return;
				}
			}
		}

		private void ManageDynamicTargets()
		{
			if (Position.MarketPosition == MarketPosition.Short)
			{
				double entry = Position.AveragePrice > 0 ? Position.AveragePrice : currentPositionEntryPrice;
				double profitPoints = entry - Low[0];

				// 1. Arm Breakeven Guard once in profit by 3.5 points ($175/contract)
				if (profitPoints >= BreakevenTriggerPoints)
					isBreakevenArmed = true;

				// 2. TP1: Scale out 1 contract at VWAP +1.0σ (must be in profit by at least 1.5 pts)
				if (!tp1Filled && upperBand1 <= (entry - 1.5))
				{
					if (Low[0] <= upperBand1)
					{
						ExitShort(1, "TP1_Dev1_Short", "Short_Absorption");
						tp1Filled        = true;
						isBreakevenArmed = true;
					}
				}

				// 3. Breakeven Guard Exit (Prevents winners from turning into losses)
				if (isBreakevenArmed && High[0] >= entry)
				{
					ExitShort("BE_Short", "Short_Absorption");
					lastExitBar = CurrentBar;
					return;
				}

				// 4. TP2: Mean Reversion to VWAP Midline
				if (currentVwap < entry && Low[0] <= currentVwap)
				{
					ExitShort("TP2_VWAP_Short", "Short_Absorption");
					lastExitBar = CurrentBar;
				}
			}
			else if (Position.MarketPosition == MarketPosition.Long)
			{
				double entry = Position.AveragePrice > 0 ? Position.AveragePrice : currentPositionEntryPrice;
				double profitPoints = High[0] - entry;

				// 1. Arm Breakeven Guard once in profit by 3.5 points ($175/contract)
				if (profitPoints >= BreakevenTriggerPoints)
					isBreakevenArmed = true;

				// 2. TP1: Scale out 1 contract at VWAP -1.0σ (must be in profit by at least 1.5 pts)
				if (!tp1Filled && lowerBand1 >= (entry + 1.5))
				{
					if (High[0] >= lowerBand1)
					{
						ExitLong(1, "TP1_Dev1_Long", "Long_Absorption");
						tp1Filled        = true;
						isBreakevenArmed = true;
					}
				}

				// 3. Breakeven Guard Exit (Prevents winners from turning into losses)
				if (isBreakevenArmed && Low[0] <= entry)
				{
					ExitLong("BE_Long", "Long_Absorption");
					lastExitBar = CurrentBar;
					return;
				}

				// 4. TP2: Mean Reversion to VWAP Midline
				if (currentVwap > entry && High[0] >= currentVwap)
				{
					ExitLong("TP2_VWAP_Long", "Long_Absorption");
					lastExitBar = CurrentBar;
				}
			}
		}

		protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
		{
			if (execution.Order != null && execution.Order.OrderState == OrderState.Filled)
			{
				if (Position.MarketPosition == MarketPosition.Flat)
				{
					lastExitBar      = CurrentBar;
					tp1Filled        = false;
					isBreakevenArmed = false;
				}
			}
		}

		private void DumpBacktestResults()
		{
			try
			{
				string dir = @"C:\Users\yasser\.gemini\antigravity\scratch\trading";
				if (!System.IO.Directory.Exists(dir))
					System.IO.Directory.CreateDirectory(dir);

				string jsonPath = System.IO.Path.Combine(dir, "latest_backtest.json");
				string txtPath  = System.IO.Path.Combine(dir, "latest_backtest_summary.txt");

				if (SystemPerformance == null || SystemPerformance.AllTrades == null)
					return;

				int totalTrades = SystemPerformance.AllTrades.Count;
				if (totalTrades == 0)
					return;

				var perf      = SystemPerformance.AllTrades.TradesPerformance;
				int winCount  = SystemPerformance.AllTrades.WinningTrades.Count;
				int lossCount = SystemPerformance.AllTrades.LosingTrades.Count;
				double winRate = totalTrades > 0 ? ((double)winCount / totalTrades * 100.0) : 0.0;

				var sb = new System.Text.StringBuilder();
				sb.AppendLine("==========================================================================================================");
				sb.AppendLine(string.Format("FLOWX ES REPORT: {0} | Completed: {1:yyyy-MM-dd HH:mm:ss}", Instrument != null ? Instrument.FullName : "ES", DateTime.Now));
				sb.AppendLine("==========================================================================================================");
				sb.AppendLine(string.Format("Net Profit:       {0:C2}", perf.NetProfit));
				sb.AppendLine(string.Format("Gross Profit:     {0:C2}", perf.GrossProfit));
				sb.AppendLine(string.Format("Gross Loss:       {0:C2}", perf.GrossLoss));
				sb.AppendLine(string.Format("Profit Factor:    {0:F2}", perf.ProfitFactor));
				sb.AppendLine(string.Format("Total Trades:     {0} (Wins: {1}, Losses: {2}, Win Rate: {3:F2}%)", totalTrades, winCount, lossCount, winRate));
				sb.AppendLine(string.Format("Total Commission: {0:C2}", perf.TotalCommission));
				sb.AppendLine(string.Format("Sharpe Ratio:     {0:F2}", perf.SharpeRatio));
				sb.AppendLine(string.Format("Sortino Ratio:    {0:F2}", perf.SortinoRatio));
				sb.AppendLine("----------------------------------------------------------------------------------------------------------");
				sb.AppendLine("Trade Log:");
				sb.AppendLine("Index | Entry Time       | Exit Time        | Dir   | Entry Px  | Exit Px   | PnL ($)     | MAE ($)   | MFE ($)");
				sb.AppendLine("----------------------------------------------------------------------------------------------------------");

				for (int i = 0; i < totalTrades; i++)
				{
					Trade t = SystemPerformance.AllTrades[i];
					sb.AppendLine(string.Format("{0,5} | {1:MM/dd HH:mm:ss} | {2:MM/dd HH:mm:ss} | {3,-5} | {4,9:F2} | {5,9:F2} | {6,11:C2} | {7,9:C2} | {8,9:C2}",
						i + 1,
						t.Entry.Time,
						t.Exit.Time,
						t.Entry.MarketPosition,
						t.Entry.Price,
						t.Exit.Price,
						t.ProfitCurrency,
						t.MaeCurrency,
						t.MfeCurrency));
				}
				sb.AppendLine("==========================================================================================================");
				System.IO.File.WriteAllText(txtPath, sb.ToString());

				var jsonSb = new System.Text.StringBuilder();
				jsonSb.AppendLine("{");
				jsonSb.AppendLine(string.Format("  \"timestamp\": \"{0}\",", DateTime.Now.ToString("o")));
				jsonSb.AppendLine(string.Format("  \"strategy\": \"FlowXAbsorptionReversal_ES\","));
				jsonSb.AppendLine(string.Format("  \"instrument\": \"{0}\",", Instrument != null ? Instrument.FullName : "ES"));
				jsonSb.AppendLine(string.Format("  \"netProfit\": {0:F2},", perf.NetProfit));
				jsonSb.AppendLine(string.Format("  \"grossProfit\": {0:F2},", perf.GrossProfit));
				jsonSb.AppendLine(string.Format("  \"grossLoss\": {0:F2},", perf.GrossLoss));
				jsonSb.AppendLine(string.Format("  \"profitFactor\": {0:F2},", perf.ProfitFactor));
				jsonSb.AppendLine(string.Format("  \"totalTrades\": {0},", totalTrades));
				jsonSb.AppendLine(string.Format("  \"winTrades\": {0},", winCount));
				jsonSb.AppendLine(string.Format("  \"lossTrades\": {0},", lossCount));
				jsonSb.AppendLine(string.Format("  \"winRate\": {0:F2},", winRate));
				jsonSb.AppendLine(string.Format("  \"commission\": {0:F2},", perf.TotalCommission));
				jsonSb.AppendLine(string.Format("  \"sharpeRatio\": {0:F2},", perf.SharpeRatio));
				jsonSb.AppendLine(string.Format("  \"sortinoRatio\": {0:F2}", perf.SortinoRatio));
				jsonSb.AppendLine("}");
				System.IO.File.WriteAllText(jsonPath, jsonSb.ToString());
			}
			catch { }
		}

		#region Strategy Properties
		[NinjaScriptProperty]
		[Range(50, 2000)]
		[Display(Name = "Min BigTrade Size (Contracts)", GroupName = "1. Order Flow Parameters", Order = 0)]
		public int MinBigTradeSize { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, 4.0)]
		[Display(Name = "VWAP Dev 2 Multiplier (Entry Zone)", GroupName = "2. VWAP Parameters", Order = 1)]
		public double VwapDev2 { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, 20.0)]
		[Display(Name = "Min Stop (Points)", GroupName = "3. Risk & Execution", Order = 2)]
		public double MinStopPoints { get; set; }

		[NinjaScriptProperty]
		[Range(2.0, 30.0)]
		[Display(Name = "Max Stop (Points)", GroupName = "3. Risk & Execution", Order = 3)]
		public double MaxStopPoints { get; set; }

		[NinjaScriptProperty]
		[Range(1, 10)]
		[Display(Name = "Quantity (Contracts)", GroupName = "3. Risk & Execution", Order = 4)]
		public int Quantity { get; set; }

		[NinjaScriptProperty]
		[Range(1, 5)]
		[Display(Name = "Max Losses Per Session", GroupName = "3. Risk & Execution", Order = 5)]
		public int MaxLossesPerDay { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, 20.0)]
		[Display(Name = "Breakeven Trigger (Points)", GroupName = "4. Profit Harvesting", Order = 6)]
		public double BreakevenTriggerPoints { get; set; }

		[NinjaScriptProperty]
		[Range(1, 20)]
		[Display(Name = "Cooldown Bars (After Exit)", GroupName = "5. Filters", Order = 7)]
		public int CooldownBars { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Require CVD Divergence", GroupName = "5. Filters", Order = 8)]
		public bool RequireCvdDivergence { get; set; }
		#endregion
	}
}
