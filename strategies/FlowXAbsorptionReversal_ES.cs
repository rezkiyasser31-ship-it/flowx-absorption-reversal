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
	/// Institutional Upgrades:
	/// 1. Dynamic Rolling Volume Normalization (Adaptive RVol Sweeps): Self-calibrates sweep threshold across seasonal volume shifts.
	/// 2. Microstructure Delta Reversal: Strict sign confirmation (currBarDelta < 0 for Short, currBarDelta > 0 for Long) to eliminate momentum blowouts.
	/// 3. Auction Market Theory Prior-Day Tracking: Retains Prior Day High, Low, Close, VWAP, and Volume for structural confluence.
	/// 4. Mean-reversion rotation targets (TP1 at ±1.0σ, TP2 at VWAP Midline, BE Guard at +3.5 pts).
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

		#region Private Fields - Prior Day Structural Reference Levels
		private double sessionHigh = double.MinValue;
		private double sessionLow  = double.MaxValue;
		private double priorDayHigh;
		private double priorDayLow;
		private double priorDayClose;
		private double priorDayVwap;
		private double priorDayVolume;
		#endregion

		#region Private Fields - Order Flow, Dynamic Sizing & BigTrade Sweeps
		private double lastBarVolume;
		private double lastTradePrice;
		private bool lastTradeWasBuy = true;
		private SMA barVolumeSma;

		// Contiguous Sweep Buffer
		private long currentSweepVol;
		private bool currentSweepIsBuy;
		private int lastBigBuyBar = -100;
		private int lastBigSellBar = -100;
		#endregion

		#region Private Fields - Funnel Diagnostics
		private int diagBarsEvaluated;
		private int diagBarsInTradingHours;
		private int diagUpperBandTouches;
		private int diagLowerBandTouches;
		private int diagBigBuySweeps;
		private int diagBigSellSweeps;
		private int diagTrappedBuyersCount;
		private int diagTrappedSellersCount;
		private int diagShortWickPass;
		private int diagLongWickPass;
		private double diagMaxTickVolume;
		private double diagMaxSweepVolume;
		private double lastEffectiveSweepThreshold;
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
				Description							= "FlowX Absorption Reversal: Institutional S&P 500 (ES) Adaptive Order Flow Engine.";
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

				// 1. Order Flow Parameters (Institutional Defaults)
				UseAdaptiveSweep					= true; // Dynamic RVol Scaling
				SweepVolumeRatio					= 0.20; // 20% of 20-bar average volume
				MinSweepFloor						= 150;  // Floor: 150 contracts
				MinBigTradeSize						= 300;  // Static fallback: 300 contracts
				StrictDeltaReversal					= true; // Require Delta sign reversal (<0 for short, >0 for long)
				RequireCvdDivergence				= true; // Require CVD exhaustion

				// 2. VWAP Parameters
				VwapDev2							= 2.00; // 2.00σ Entry Zone (standard institutional deviation)

				// 3. Risk & Structural Execution (ES Scale: $50/pt)
				MinStopPoints						= 5.0;  // 20 ticks = $250/contract
				MaxStopPoints						= 6.0;  // 24 ticks = $300/contract
				Quantity							= 2;    // 2 contracts
				MaxLossesPerDay						= 2;    // Max losses per session

				// 4. Profit Harvesting
				BreakevenTriggerPoints				= 3.5;  // Lock Breakeven at +3.5 pts (+14 ticks = $175/contract)

				// 5. Microstructure & Market Structure Filters
				CooldownBars						= 3;    // Cooldown after an exit
				MinWickPoints						= 0.75; // Minimum rejection wick (3 ticks = 0.75 pts)
				TrappedBarsLookback					= 2;    // Reaction window for absorption
				OpeningBufferMinutes				= 45;   // Skip opening drive
				EnableTrendFilter					= true; // Protect against fading strong trend days
				TrendSlopeThreshold					= 1.0;  // 1.0 pt VWAP slope indicates trend
				SlopeLookbackBars					= 20;   // 20-bar lookback for VWAP slope
				RequirePriorDayConfluence			= false;// Optional horizontal profile confluence

				// 6. Intraday Institutional Window (10:30 - 14:00 EST / 17:00 - 20:30 chart time)
				UseTimeFilter						= true;
				TradeStartHour						= 17;
				TradeStartMinute					= 0;
				TradeEndHour						= 20;
				TradeEndMinute						= 30;

				// 7. MT5 Bridge & Alerts
				EnableBridge						= true;
				BridgeWebhookUrl					= "http://127.0.0.1:5005/trade";
				Mt5Lots								= 2.0;
				TelegramBotToken					= "";
				TelegramChatId						= "";
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
				barVolumeSma    = SMA(Volume, 20);
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
			if (CurrentBar < 20)
				return;

			// --- 1. Session Detection, Rollover & Structural Reference Capture ---
			if (sessionIterator == null)
				sessionIterator = new SessionIterator(Bars);

			if (Bars.IsFirstBarOfSession || currentTradingDay == DateTime.MinValue || Time[0].Date != currentTradingDay.Date)
			{
				if (currentTradingDay != DateTime.MinValue && cumVolume > 0)
				{
					priorDayHigh   = sessionHigh;
					priorDayLow    = sessionLow;
					priorDayClose  = Close[1];
					priorDayVwap   = currentVwap;
					priorDayVolume = cumVolume;
				}

				sessionHigh       = High[0];
				sessionLow        = Low[0];
				currentTradingDay = Time[0].Date;
				try
				{
					sessionIterator.GetNextSession(Time[0], true);
				}
				catch { }
				ClearSessionState();
			}
			else
			{
				if (High[0] > sessionHigh) sessionHigh = High[0];
				if (Low[0]  < sessionLow)  sessionLow  = Low[0];
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

			// --- 3. Session Boundaries & EOD Mandatory Flatten ---
			bool sessionBoundsValid = (sessionIterator != null && sessionIterator.ActualSessionEnd > sessionIterator.ActualSessionBegin);
			double minutesToSessionEnd = 999;
			double minutesFromOpen = 999;

			if (sessionBoundsValid)
			{
				minutesToSessionEnd = (sessionIterator.ActualSessionEnd - Time[0]).TotalMinutes;
				minutesFromOpen = (Time[0] - sessionIterator.ActualSessionBegin).TotalMinutes;

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

			// Aggressor Classification (Lee-Ready Uptick/Downtick Rule)
			bool isBuy = lastTradeWasBuy;
			if (lastTradePrice <= 0)
			{
				lastTradePrice = Close[0];
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

			// --- 5. Adaptive Rolling Volume Sweep Threshold ---
			double effectiveSweepThreshold = MinBigTradeSize;
			if (UseAdaptiveSweep && barVolumeSma != null && CurrentBar >= 20)
			{
				double dynamicTarget = barVolumeSma[0] * SweepVolumeRatio;
				effectiveSweepThreshold = Math.Max(MinSweepFloor, dynamicTarget);
			}
			lastEffectiveSweepThreshold = effectiveSweepThreshold;

			// Funnel Diagnostics Tracking
			diagBarsEvaluated++;
			if (currentTickVolume > diagMaxTickVolume) diagMaxTickVolume = currentTickVolume;
			if (currentSweepVol > diagMaxSweepVolume) diagMaxSweepVolume = currentSweepVol;

			if (currentTickVolume >= effectiveSweepThreshold || currentSweepVol >= effectiveSweepThreshold)
			{
				if (isBuy)
				{
					lastBigBuyBar = CurrentBar;
					diagBigBuySweeps++;
				}
				else
				{
					lastBigSellBar = CurrentBar;
					diagBigSellSweeps++;
				}
			}

			// --- 6. Closed-Form FlowX Session VWAP Math ---
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

				if (High[0] >= upperBand2) diagUpperBandTouches++;
				if (Low[0] <= lowerBand2)  diagLowerBandTouches++;
			}

			// --- 7. Position & Target Management ---
			ManageDynamicTargets();

			// --- 8. Signal Execution ---
			if (Position.MarketPosition == MarketPosition.Flat)
			{
				if (sessionLossCount >= MaxLossesPerDay)
					return;

				if (CurrentBar == lastEntryBar || CurrentBar <= lastExitBar + CooldownBars)
					return;

				// Intraday Institutional Window Filter (11:30 - 14:30 EST / 18:00 - 20:30 chart time)
				if (UseTimeFilter)
				{
					int barMinutes   = Time[0].Hour * 60 + Time[0].Minute;
					int startMinutes = TradeStartHour * 60 + TradeStartMinute;
					int endMinutes   = TradeEndHour * 60 + TradeEndMinute;
					if (barMinutes < startMinutes || barMinutes > endMinutes)
						return;
				}

				// Skip opening rush and closing volatility ONLY if valid session bounds exist
				if (sessionBoundsValid)
				{
					if (minutesFromOpen >= 0 && minutesFromOpen < OpeningBufferMinutes)
						return;
					if (minutesToSessionEnd >= 0 && minutesToSessionEnd < 30)
						return;
				}

				// VWAP Trend Regime Classification
				bool isBullTrend = false;
				bool isBearTrend = false;
				if (EnableTrendFilter && CurrentBar >= SlopeLookbackBars && Values[0][SlopeLookbackBars] > 0)
				{
					double vwapSlope = currentVwap - Values[0][SlopeLookbackBars];
					if (vwapSlope >= TrendSlopeThreshold)
						isBullTrend = true;
					else if (vwapSlope <= -TrendSlopeThreshold)
						isBearTrend = true;
				}

				diagBarsInTradingHours++;
				CheckForESEntries(isBullTrend, isBearTrend, effectiveSweepThreshold);
			}
		}

		private void CheckForESEntries(bool isBullTrend, bool isBearTrend, double effectiveSweepThreshold)
		{
			if (currentVwap <= 0 || upperBand2 <= 0 || lowerBand2 <= 0)
				return;

			// ==========================================
			// SHORT SETUP: Bearish Absorption at Extreme VWAP Band
			// ==========================================
			if (!isBullTrend)
			{
				bool testedUpperBand = (High[0] >= upperBand2 || High[1] >= upperBand2);
				bool buyersTrapped   = (CurrentBar - lastBigBuyBar <= TrappedBarsLookback);

				if (testedUpperBand && buyersTrapped) diagTrappedBuyersCount++;

				double upperWick     = High[0] - Math.Max(Open[0], Close[0]);
				bool hasUpperWick    = (upperWick >= MinWickPoints);
				if (hasUpperWick) diagShortWickPass++;

				bool isBearishBar    = (Close[0] < Open[0]) && (Close[0] < High[0] - 0.50);

				// Institutional Delta Reversal: Sellers must take control (delta < 0)
				bool cvdExhaustedShort;
				if (StrictDeltaReversal)
				{
					cvdExhaustedShort = (currBarDelta < 0);
				}
				else
				{
					cvdExhaustedShort = !RequireCvdDivergence || (currBarDelta <= (effectiveSweepThreshold * 0.4));
				}

				// Structural Confluence: Prior Day High sweep or neutral
				bool structuralResistance = !RequirePriorDayConfluence || priorDayHigh <= 0 || (High[0] >= priorDayHigh - (2 * TickSize));

				if (testedUpperBand && buyersTrapped && hasUpperWick && isBearishBar && cvdExhaustedShort && structuralResistance)
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

						BroadcastSignal("SELL", stopPoints, 10.0);
						EnterShort(Quantity, "Short_Absorption");
						return;
					}
				}
			}

			// ==========================================
			// LONG SETUP: Bullish Absorption at Extreme VWAP Band
			// ==========================================
			if (!isBearTrend)
			{
				bool testedLowerBand = (Low[0] <= lowerBand2 || Low[1] <= lowerBand2);
				bool sellersTrapped  = (CurrentBar - lastBigSellBar <= TrappedBarsLookback);

				if (testedLowerBand && sellersTrapped) diagTrappedSellersCount++;

				double lowerWick     = Math.Min(Open[0], Close[0]) - Low[0];
				bool hasLowerWick    = (lowerWick >= MinWickPoints);
				if (hasLowerWick) diagLongWickPass++;

				bool isBullishBar    = (Close[0] > Open[0]) && (Close[0] > Low[0] + 0.50);

				// Institutional Delta Reversal: Buyers must take control (delta > 0)
				bool cvdExhaustedLong;
				if (StrictDeltaReversal)
				{
					cvdExhaustedLong = (currBarDelta > 0);
				}
				else
				{
					cvdExhaustedLong = !RequireCvdDivergence || (currBarDelta >= -(effectiveSweepThreshold * 0.4));
				}

				// Structural Confluence: Prior Day Low sweep or neutral
				bool structuralSupport = !RequirePriorDayConfluence || priorDayLow <= 0 || (Low[0] <= priorDayLow + (2 * TickSize));

				if (testedLowerBand && sellersTrapped && hasLowerWick && isBullishBar && cvdExhaustedLong && structuralSupport)
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

						BroadcastSignal("BUY", stopPoints, 10.0);
						EnterLong(Quantity, "Long_Absorption");
						return;
					}
				}
			}
		}

		private void ManageDynamicTargets()
		{
			if (Position.MarketPosition == MarketPosition.Short)
			{
				double entry = Position.AveragePrice > 0 ? Position.AveragePrice : currentPositionEntryPrice;
				double profitPoints = entry - Low[0];

				// 1. Arm Breakeven Guard once in profit by BreakevenTriggerPoints (3.5 pts = $175)
				if (profitPoints >= BreakevenTriggerPoints)
				{
					if (!isBreakevenArmed)
					{
						isBreakevenArmed = true;
						BroadcastSignal("BREAKEVEN", 0, 0);
					}
				}

				// 2. TP1: Scale out 1 contract at VWAP +1.0σ (must be in profit by at least 1.5 pts)
				if (!tp1Filled && upperBand1 <= (entry - 1.5))
				{
					if (Low[0] <= upperBand1)
					{
						ExitShort(1, "TP1_Dev1_Short", "Short_Absorption");
						tp1Filled        = true;
						isBreakevenArmed = true;
						BroadcastSignal("CLOSE_HALF", 0, 0);
					}
				}

				// 3. Breakeven Guard Exit (Prevents winners from turning into losses)
				if (isBreakevenArmed && High[0] >= entry)
				{
					ExitShort("BE_Short", "Short_Absorption");
					lastExitBar = CurrentBar;
					BroadcastSignal("CLOSE_ALL", 0, 0);
					return;
				}

				// 4. TP2: Mean Reversion to VWAP Midline
				if (currentVwap < entry && Low[0] <= currentVwap)
				{
					ExitShort("TP2_VWAP_Short", "Short_Absorption");
					lastExitBar = CurrentBar;
					BroadcastSignal("CLOSE_ALL", 0, 0);
				}
			}
			else if (Position.MarketPosition == MarketPosition.Long)
			{
				double entry = Position.AveragePrice > 0 ? Position.AveragePrice : currentPositionEntryPrice;
				double profitPoints = High[0] - entry;

				// 1. Arm Breakeven Guard once in profit by BreakevenTriggerPoints (3.5 pts = $175)
				if (profitPoints >= BreakevenTriggerPoints)
				{
					if (!isBreakevenArmed)
					{
						isBreakevenArmed = true;
						BroadcastSignal("BREAKEVEN", 0, 0);
					}
				}

				// 2. TP1: Scale out 1 contract at VWAP -1.0σ (must be in profit by at least 1.5 pts)
				if (!tp1Filled && lowerBand1 >= (entry + 1.5))
				{
					if (High[0] >= lowerBand1)
					{
						ExitLong(1, "TP1_Dev1_Long", "Long_Absorption");
						tp1Filled        = true;
						isBreakevenArmed = true;
						BroadcastSignal("CLOSE_HALF", 0, 0);
					}
				}

				// 3. Breakeven Guard Exit (Prevents winners from turning into losses)
				if (isBreakevenArmed && Low[0] <= entry)
				{
					ExitLong("BE_Long", "Long_Absorption");
					lastExitBar = CurrentBar;
					BroadcastSignal("CLOSE_ALL", 0, 0);
					return;
				}

				// 4. TP2: Mean Reversion to VWAP Midline
				if (currentVwap > entry && High[0] >= currentVwap)
				{
					ExitLong("TP2_VWAP_Long", "Long_Absorption");
					lastExitBar = CurrentBar;
					BroadcastSignal("CLOSE_ALL", 0, 0);
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
					BroadcastSignal("CLOSE_ALL", 0, 0);
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

				if (SystemPerformance == null || SystemPerformance.AllTrades == null || Bars == null || Bars.Count == 0)
					return;

				int totalTrades = SystemPerformance.AllTrades.Count;
				if (totalTrades == 0)
				{
					var sb0 = new System.Text.StringBuilder();
					sb0.AppendLine("==========================================================================================================");
					sb0.AppendLine(string.Format("COMPLETED on {0} at {1:yyyy-MM-dd HH:mm:ss}: 0 Trades Executed (Total Bars Loaded: {2}).", Instrument != null ? Instrument.FullName : "ES", DateTime.Now, Bars != null ? Bars.Count : 0));
					sb0.AppendLine("==========================================================================================================");
					sb0.AppendLine("DIAGNOSTIC FUNNEL ANALYSIS:");
					sb0.AppendLine(string.Format("  Total Bars Evaluated:       {0}", diagBarsEvaluated));
					sb0.AppendLine(string.Format("  Bars in Trading Hours:      {0}", diagBarsInTradingHours));
					sb0.AppendLine(string.Format("  Max Single Tick Volume:     {0:F0}", diagMaxTickVolume));
					sb0.AppendLine(string.Format("  Max Contiguous Sweep Vol:   {0:F0}", diagMaxSweepVolume));
					sb0.AppendLine(string.Format("  Adaptive Sweep Enabled:     {0} (Ratio: {1:F2}, Floor: {2})", UseAdaptiveSweep, SweepVolumeRatio, MinSweepFloor));
					sb0.AppendLine(string.Format("  Static MinBigTradeSize:     {0}", MinBigTradeSize));
					sb0.AppendLine(string.Format("  Last Effective Threshold:   {0:F0}", lastEffectiveSweepThreshold));
					sb0.AppendLine(string.Format("  Big Buy Sweeps Detected:    {0}", diagBigBuySweeps));
					sb0.AppendLine(string.Format("  Big Sell Sweeps Detected:   {0}", diagBigSellSweeps));
					sb0.AppendLine(string.Format("  VwapDev2 Parameter:         {0:F2}", VwapDev2));
					sb0.AppendLine(string.Format("  Upper Band (+{0:F1}σ) Touches: {1}", VwapDev2, diagUpperBandTouches));
					sb0.AppendLine(string.Format("  Lower Band (-{0:F1}σ) Touches: {1}", VwapDev2, diagLowerBandTouches));
					sb0.AppendLine(string.Format("  Trapped Buyers Candidate:   {0}", diagTrappedBuyersCount));
					sb0.AppendLine(string.Format("  Trapped Sellers Candidate:  {0}", diagTrappedSellersCount));
					sb0.AppendLine(string.Format("  Short Wick (Pass):          {0}", diagShortWickPass));
					sb0.AppendLine(string.Format("  Long Wick (Pass):           {0}", diagLongWickPass));
					sb0.AppendLine(string.Format("  Strict Delta Reversal:      {0}", StrictDeltaReversal));
					sb0.AppendLine(string.Format("  Prior Day Confluence:       {0}", RequirePriorDayConfluence));
					sb0.AppendLine("==========================================================================================================");
					System.IO.File.WriteAllText(txtPath, sb0.ToString());
					return;
				}

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

				// Append to persistent ES Optimization Log CSV
				string optCsvPath = System.IO.Path.Combine(dir, "optimization_log_es.csv");
				bool fileExists   = System.IO.File.Exists(optCsvPath);
				lock (typeof(FlowXAbsorptionReversal_ES))
				{
					using (var sw = new System.IO.StreamWriter(optCsvPath, true))
					{
						if (!fileExists)
						{
							sw.WriteLine("Timestamp,Instrument,VwapDev2,MinBigTradeSize,MinStopPoints,BreakevenTrigger,MaxLosses,SweepRatio,NetProfit,GrossProfit,GrossLoss,ProfitFactor,TotalTrades,WinTrades,LossTrades,WinRate,Commission,Sharpe,Sortino");
						}
						sw.WriteLine(string.Format("{0},{1},{2:F2},{3},{4:F2},{5:F2},{6},{7:F2},{8:F2},{9:F2},{10:F2},{11:F2},{12},{13},{14},{15:F2},{16:F2},{17:F2},{18:F2}",
							DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
							Instrument != null ? Instrument.FullName : "ES",
							VwapDev2,
							MinBigTradeSize,
							MinStopPoints,
							BreakevenTriggerPoints,
							MaxLossesPerDay,
							SweepVolumeRatio,
							perf.NetProfit,
							perf.GrossProfit,
							perf.GrossLoss,
							perf.ProfitFactor,
							totalTrades,
							winCount,
							lossCount,
							winRate,
							perf.TotalCommission,
							perf.SharpeRatio,
							perf.SortinoRatio));
					}
				}
			}
			catch { }
		}

		#region Strategy Properties
		[NinjaScriptProperty]
		[Display(Name = "Use Adaptive Sweep (RVol)", GroupName = "1. Order Flow Parameters", Order = 0)]
		public bool UseAdaptiveSweep { get; set; }

		[NinjaScriptProperty]
		[Range(0.05, 0.50)]
		[Display(Name = "Sweep Volume Ratio", GroupName = "1. Order Flow Parameters", Order = 1)]
		public double SweepVolumeRatio { get; set; }

		[NinjaScriptProperty]
		[Range(50, 500)]
		[Display(Name = "Min Sweep Floor (Contracts)", GroupName = "1. Order Flow Parameters", Order = 2)]
		public int MinSweepFloor { get; set; }

		[NinjaScriptProperty]
		[Range(50, 2000)]
		[Display(Name = "Static Min BigTrade Size", GroupName = "1. Order Flow Parameters", Order = 3)]
		public int MinBigTradeSize { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Strict Delta Reversal (Sign Flip)", GroupName = "1. Order Flow Parameters", Order = 4)]
		public bool StrictDeltaReversal { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Require CVD Divergence", GroupName = "1. Order Flow Parameters", Order = 5)]
		public bool RequireCvdDivergence { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, 4.0)]
		[Display(Name = "VWAP Dev 2 Multiplier (Entry Zone)", GroupName = "2. VWAP Parameters", Order = 6)]
		public double VwapDev2 { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, 20.0)]
		[Display(Name = "Min Stop (Points)", GroupName = "3. Risk & Execution", Order = 7)]
		public double MinStopPoints { get; set; }

		[NinjaScriptProperty]
		[Range(2.0, 30.0)]
		[Display(Name = "Max Stop (Points)", GroupName = "3. Risk & Execution", Order = 8)]
		public double MaxStopPoints { get; set; }

		[NinjaScriptProperty]
		[Range(1, 10)]
		[Display(Name = "Quantity (Contracts)", GroupName = "3. Risk & Execution", Order = 9)]
		public int Quantity { get; set; }

		[NinjaScriptProperty]
		[Range(1, 5)]
		[Display(Name = "Max Losses Per Session", GroupName = "3. Risk & Execution", Order = 10)]
		public int MaxLossesPerDay { get; set; }

		[NinjaScriptProperty]
		[Range(1.0, 20.0)]
		[Display(Name = "Breakeven Trigger (Points)", GroupName = "4. Profit Harvesting", Order = 11)]
		public double BreakevenTriggerPoints { get; set; }

		[NinjaScriptProperty]
		[Range(1, 20)]
		[Display(Name = "Cooldown Bars (After Exit)", GroupName = "5. Filters", Order = 12)]
		public int CooldownBars { get; set; }

		[NinjaScriptProperty]
		[Range(0.25, 2.0)]
		[Display(Name = "Min Rejection Wick (Points)", GroupName = "5. Filters", Order = 13)]
		public double MinWickPoints { get; set; }

		[NinjaScriptProperty]
		[Range(1, 5)]
		[Display(Name = "Trapped Bars Lookback", GroupName = "5. Filters", Order = 14)]
		public int TrappedBarsLookback { get; set; }

		[NinjaScriptProperty]
		[Range(0, 120)]
		[Display(Name = "Opening Buffer (Minutes)", GroupName = "5. Filters", Order = 15)]
		public int OpeningBufferMinutes { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Enable Trend Filter (VWAP Slope)", GroupName = "5. Filters", Order = 16)]
		public bool EnableTrendFilter { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, 10.0)]
		[Display(Name = "Trend Slope Threshold (Pts)", GroupName = "5. Filters", Order = 17)]
		public double TrendSlopeThreshold { get; set; }

		[NinjaScriptProperty]
		[Range(5, 100)]
		[Display(Name = "Slope Lookback Bars", GroupName = "5. Filters", Order = 18)]
		public int SlopeLookbackBars { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Require Prior Day Confluence", GroupName = "5. Filters", Order = 19)]
		public bool RequirePriorDayConfluence { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Use Time Filter (Institutional Window)", GroupName = "6. Session Window", Order = 20)]
		public bool UseTimeFilter { get; set; }

		[NinjaScriptProperty]
		[Range(0, 23)]
		[Display(Name = "Trade Start Hour", GroupName = "6. Session Window", Order = 21)]
		public int TradeStartHour { get; set; }

		[NinjaScriptProperty]
		[Range(0, 59)]
		[Display(Name = "Trade Start Minute", GroupName = "6. Session Window", Order = 22)]
		public int TradeStartMinute { get; set; }

		[NinjaScriptProperty]
		[Range(0, 23)]
		[Display(Name = "Trade End Hour", GroupName = "6. Session Window", Order = 23)]
		public int TradeEndHour { get; set; }

		[NinjaScriptProperty]
		[Range(0, 59)]
		[Display(Name = "Trade End Minute", GroupName = "6. Session Window", Order = 24)]
		public int TradeEndMinute { get; set; }

		#region Bridge & Alerts Properties
		[NinjaScriptProperty]
		[Display(Name = "Enable MT5 Bridge", GroupName = "7. MT5 Bridge & Alerts", Order = 25)]
		public bool EnableBridge { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Bridge Webhook URL", GroupName = "7. MT5 Bridge & Alerts", Order = 26)]
		public string BridgeWebhookUrl { get; set; }

		[NinjaScriptProperty]
		[Range(0.1, 50.0)]
		[Display(Name = "MT5 Lots (0.10 to 50)", GroupName = "7. MT5 Bridge & Alerts", Order = 27)]
		public double Mt5Lots { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Telegram Bot Token", GroupName = "7. MT5 Bridge & Alerts", Order = 28)]
		public string TelegramBotToken { get; set; }

		[NinjaScriptProperty]
		[Display(Name = "Telegram Chat ID", GroupName = "7. MT5 Bridge & Alerts", Order = 29)]
		public string TelegramChatId { get; set; }
		#endregion

		private void BroadcastSignal(string action, double stopPoints, double tpPoints)
		{
			// CRITICAL: Only broadcast during live realtime execution (ignore historical bar catch-up)
			if (State != State.Realtime)
				return;

			// 1. Direct MT5 Python Bridge Webhook
			if (EnableBridge && !string.IsNullOrEmpty(BridgeWebhookUrl))
			{
				try
				{
					using (var client = new System.Net.WebClient())
					{
						client.Headers[System.Net.HttpRequestHeader.ContentType] = "application/json";
						string payload = string.Format(
							System.Globalization.CultureInfo.InvariantCulture,
							"{{\"action\":\"{0}\",\"volume\":{1:F2},\"stop_points\":{2:F2},\"tp_points\":{3:F2},\"source\":\"FlowX_ES\"}}",
							action, Mt5Lots, stopPoints, tpPoints);
						client.UploadStringAsync(new Uri(BridgeWebhookUrl), "POST", payload);
					}
				}
				catch { }
			}

			// 2. Direct Telegram Broadcast
			if (!string.IsNullOrEmpty(TelegramBotToken) && !string.IsNullOrEmpty(TelegramChatId))
			{
				try
				{
					using (var client = new System.Net.WebClient())
					{
						string text = string.Format(
							System.Globalization.CultureInfo.InvariantCulture,
							"⚡ *FLOWX INSTITUTIONAL SIGNAL* ⚡%0A• Direction: *{0}*%0A• Stop: {1:F2} pts%0A• Target: {2:F2} pts%0A• Lots: {3:F2}",
							action, stopPoints, tpPoints, Mt5Lots);
						string url = string.Format(
							"https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}&parse_mode=Markdown",
							TelegramBotToken, TelegramChatId, text);
						client.DownloadStringAsync(new Uri(url));
					}
				}
				catch { }
			}
		}
		#endregion
	}
}
