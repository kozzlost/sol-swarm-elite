"""
SOL-SWARM Elite - Example Usage and Testing Script
"""

from datetime import datetime
from src.types import TradeSignal
from src.command_center import CommandCenter


def create_sample_signal(
    token: str = "SAMPLE",
    price: float = 0.00001,
    liquidity: float = 100000,
    honeypot_score: float = 0.2,
    sentiment_score: float = 0.65
) -> TradeSignal:
    """Create a sample trade signal for testing"""
    
    return TradeSignal(
        token=token,
        token_address=f"0x{'0'*40}",  # Placeholder address
        liquidity=liquidity,
        market_cap=liquidity * 100,
        holder_count=500,
        volume_24h=liquidity * 0.5,
        price=price,
        timestamp=datetime.now().isoformat(),
        honeypot_score=honeypot_score,
        rug_pull_risk="low",
        contract_verified=True,
        momentum=75.0,
        volume_ratio=1.2,
        sentiment_score=sentiment_score,
        social_mentions=25
    )


def test_basic_pipeline():
    """Test basic trading pipeline"""
    
    print("\n" + "=" * 70)
    print("TEST 1: Basic Trading Pipeline")
    print("=" * 70)
    
    # Initialize Command Center
    cc = CommandCenter()
    
    # Create and process a good signal
    good_signal = create_sample_signal(
        token="GOODTOKEN",
        liquidity=150000,
        honeypot_score=0.1,
        sentiment_score=0.75
    )
    
    print("\n[TEST] Processing good signal...")
    result = cc.process_signal(good_signal)
    print(f"Result: {'✓ EXECUTED' if result else '✗ REJECTED'}")
    
    # Create and process a risky signal
    risky_signal = create_sample_signal(
        token="RISKTOKEN",
        liquidity=30000,  # Too low
        honeypot_score=0.85  # Too high
    )
    
    print("\n[TEST] Processing risky signal...")
    result = cc.process_signal(risky_signal)
    print(f"Result: {'✓ EXECUTED' if result else '✗ REJECTED'}")
    
    # Print status
    cc.print_status()
    
    return cc


def test_sentiment_analysis():
    """Test sentiment analysis capabilities"""
    
    print("\n" + "=" * 70)
    print("TEST 2: Sentiment Analysis")
    print("=" * 70)
    
    from src.agents.sentiment_agent import SentimentAgent
    
    sentiment = SentimentAgent()
    
    # Sample texts
    positive_texts = [
        "I love this token! Great project",
        "Amazing community, very bullish",
        "Best memecoin ever, moon soon",
        "Excellent development team, buying more",
        "Revolutionary technology, highly recommended"
    ]
    
    negative_texts = [
        "This is a complete scam",
        "I lost all my money, terrible project",
        "Worst investment ever, stay away",
        "Red flags everywhere, don't buy",
        "Pump and dump scheme detected"
    ]
    
    mixed_texts = [
        "Good potential but risky",
        "Interesting idea, needs work",
        "Has pros and cons",
        "Could go either way",
        "Decent project with challenges"
    ]
    
    # Test positive sentiment
    print("\n[TEST] Analyzing POSITIVE sentiment...")
    result_pos = sentiment.analyze("TOKEN_BULLISH", positive_texts)
    print(f"Score: {result_pos.overall_score:.2f} | Positive: {result_pos.positive_percentage:.0f}%")
    
    # Test negative sentiment
    print("\n[TEST] Analyzing NEGATIVE sentiment...")
    result_neg = sentiment.analyze("TOKEN_BEARISH", negative_texts)
    print(f"Score: {result_neg.overall_score:.2f} | Positive: {result_neg.positive_percentage:.0f}%")
    
    # Test mixed sentiment
    print("\n[TEST] Analyzing MIXED sentiment...")
    result_mix = sentiment.analyze("TOKEN_MIXED", mixed_texts)
    print(f"Score: {result_mix.overall_score:.2f} | Positive: {result_mix.positive_percentage:.0f}%")


def test_ceo_decision_making():
    """Test CEO Agent decision making"""
    
    print("\n" + "=" * 70)
    print("TEST 3: CEO Agent Decision Making")
    print("=" * 70)
    
    from src.agents.ceo_agent import CEOAgent
    
    ceo = CEOAgent()
    
    test_cases = [
        {
            "name": "Perfect Signal",
            "signal": create_sample_signal(
                token="PERFECT",
                liquidity=500000,
                honeypot_score=0.05,
                sentiment_score=0.8
            )
        },
        {
            "name": "Low Liquidity",
            "signal": create_sample_signal(
                token="LOWLIQ",
                liquidity=20000  # Below threshold
            )
        },
        {
            "name": "High Honeypot Risk",
            "signal": create_sample_signal(
                token="HONEYPOT",
                honeypot_score=0.9  # Too high
            )
        },
        {
            "name": "Poor Sentiment",
            "signal": create_sample_signal(
                token="BEARISH",
                sentiment_score=0.3  # Too low
            )
        }
    ]
    
    for test_case in test_cases:
        print(f"\n[TEST] {test_case['name']}")
        decision = ceo.allocate_resources(test_case['signal'])
        print(f"Decision: {decision.action.value.upper()}")
        print(f"Reason: {decision.reason}")
        print(f"Risk Level: {decision.risk_level}/100")


def test_market_monitoring():
    """Test market condition monitoring"""
    
    print("\n" + "=" * 70)
    print("TEST 4: Market Monitoring")
    print("=" * 70)
    
    cc = CommandCenter()
    
    test_scenarios = [
        {
            "name": "Normal Market",
            "volatility": 12.5,
            "market_change": 2.3
        },
        {
            "name": "High Volatility",
            "volatility": 25.0,
            "market_change": 5.5
        },
        {
            "name": "Market Crash",
            "volatility": 45.0,
            "market_change": -15.0
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n[TEST] {scenario['name']}")
        print(f"Volatility: {scenario['volatility']:.1f}%")
        print(f"Market Change: {scenario['market_change']:+.1f}%")
        
        cc.update_market_conditions(scenario['volatility'], scenario['market_change'])
        
        print(f"Market Condition: {cc.ceo.market_condition.upper()}")
        print(f"System Health: {cc.ceo.system_health.upper()}")
        print(f"Trading Paused: {cc.ceo.trading_paused}")


def full_integration_test():
    """Run full integration test"""
    
    print("\n" + "=" * 70)
    print("FULL INTEGRATION TEST")
    print("=" * 70)
    
    cc = CommandCenter()
    
    # Generate multiple signals
    tokens = [
        ("ALPHA", 0.00001, 200000, 0.15, 0.72),
        ("BETA", 0.00005, 150000, 0.25, 0.65),
        ("GAMMA", 0.000001, 80000, 0.35, 0.70),
        ("DELTA", 0.0002, 30000, 0.85, 0.40),  # Will be rejected
        ("EPSILON", 0.00003, 250000, 0.10, 0.78),
    ]
    
    print("\nProcessing 5 signals...")
    for token, price, liquidity, honeypot, sentiment in tokens:
        signal = create_sample_signal(
            token=token,
            price=price,
            liquidity=liquidity,
            honeypot_score=honeypot,
            sentiment_score=sentiment
        )
        cc.process_signal(signal)
    
    # Monitor positions
    print("\nMonitoring positions...")
    cc.monitor_positions()
    
    # Final status
    print("\nGenerating final report...")
    report = cc.get_detailed_report()
    
    print("\n" + "=" * 70)
    print("INTEGRATION TEST RESULTS")
    print("=" * 70)
    print(f"Signals Processed: {report['pipeline']['signals_processed']}")
    print(f"Trades Executed: {report['pipeline']['trades_executed']}")
    print(f"Trades Failed: {report['pipeline']['trades_failed']}")
    print(f"Success Rate: {report['pipeline']['success_rate']*100:.1f}%")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    
    print("\n" + "=" * 70)
    print("SOL-SWARM Elite - System Tests")
    print("=" * 70)
    
    # Run tests
    test_basic_pipeline()
    test_sentiment_analysis()
    test_ceo_decision_making()
    test_market_monitoring()
    full_integration_test()
    
    print("\n✓ All tests completed!")
