import os
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Import tools and prompts
from tools.general_tools import get_config_value, write_config_value
from prompts.agent_prompt import all_nasdaq_100_symbols


# Agent class mapping table - for dynamic import and instantiation
AGENT_REGISTRY = {
    "BaseAgent": {
        "module": "agent.base_agent.base_agent",
        "class": "BaseAgent"
    },
    "TraditionalAgent": {
        "module": "agent.traditional_agent.traditional_agent",
        "class": "TraditionalAgent"
    },
    "MomentumAgent": {
        "module": "agent.momentum_agent.momentum_agent",
        "class": "MomentumAgent"
    },
}


def get_agent_class(agent_type):
    """
    Dynamically import and return the corresponding class based on agent type name
    
    Args:
        agent_type: Agent type name (e.g., "BaseAgent")
        
    Returns:
        Agent class
        
    Raises:
        ValueError: If agent type is not supported
        ImportError: If unable to import agent module
    """
    if agent_type not in AGENT_REGISTRY:
        supported_types = ", ".join(AGENT_REGISTRY.keys())
        raise ValueError(
            f"❌ Unsupported agent type: {agent_type}\n"
            f"   Supported types: {supported_types}"
        )
    
    agent_info = AGENT_REGISTRY[agent_type]
    module_path = agent_info["module"]
    class_name = agent_info["class"]
    
    try:
        # Dynamic import module
        import importlib
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        print(f"✅ Successfully loaded Agent class: {agent_type} (from {module_path})")
        return agent_class
    except ImportError as e:
        raise ImportError(f"❌ Unable to import agent module {module_path}: {e}")
    except AttributeError as e:
        raise AttributeError(f"❌ Class {class_name} not found in module {module_path}: {e}")


def load_config(config_path=None):
    """
    Load configuration file from configs directory
    
    Args:
        config_path: Configuration file path, if None use default config
        
    Returns:
        dict: Configuration dictionary
    """
    if config_path is None:
        # Default configuration file path
        config_path = Path(__file__).parent / "configs" / "default_config.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        print(f"❌ Configuration file does not exist: {config_path}")
        exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ Successfully loaded configuration file: {config_path}")
        return config
    except json.JSONDecodeError as e:
        print(f"❌ Configuration file JSON format error: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Failed to load configuration file: {e}")
        exit(1)


async def main(config_path=None):
    """Run trading experiment using BaseAgent class
    
    Args:
        config_path: Configuration file path, if None use default config
    """
    # Load configuration file
    config = load_config(config_path)
    
    # Get Agent type
    agent_type = config.get("agent_type", "BaseAgent")
    try:
        AgentClass = get_agent_class(agent_type)
    except (ValueError, ImportError, AttributeError) as e:
        print(str(e))
        exit(1)
    
    # Get date range from configuration file
    INIT_DATE = config["date_range"]["init_date"]
    END_DATE = config["date_range"]["end_date"]
    
    # Environment variables can override dates in configuration file
    if os.getenv("INIT_DATE"):
        INIT_DATE = os.getenv("INIT_DATE")
        print(f"⚠️  Using environment variable to override INIT_DATE: {INIT_DATE}")
    if os.getenv("END_DATE"):
        END_DATE = os.getenv("END_DATE")
        print(f"⚠️  Using environment variable to override END_DATE: {END_DATE}")
    
    # Validate date range
    INIT_DATE_obj = datetime.strptime(INIT_DATE, "%Y-%m-%d").date()
    END_DATE_obj = datetime.strptime(END_DATE, "%Y-%m-%d").date()
    if INIT_DATE_obj > END_DATE_obj:
        print("❌ INIT_DATE is greater than END_DATE")
        exit(1)
 
    # Get model list from configuration file (only select enabled models)
    enabled_models = [
        model for model in config["models"] 
        if model.get("enabled", True)
    ]
    
    # Get agent configuration
    agent_config = config.get("agent_config", {})
    log_config = config.get("log_config", {})
    max_steps = agent_config.get("max_steps", 10)
    max_retries = agent_config.get("max_retries", 3)
    base_delay = agent_config.get("base_delay", 0.5)
    initial_cash = agent_config.get("initial_cash", 10000.0)
    
    # Display enabled model information
    model_names = [m.get("name", m.get("signature")) for m in enabled_models]
    
    print("🚀 Starting trading experiment")
    print(f"🤖 Agent type: {agent_type}")
    print(f"📅 Date range: {INIT_DATE} to {END_DATE}")
    print(f"🤖 Model list: {model_names}")
    print(f"⚙️  Agent config: max_steps={max_steps}, max_retries={max_retries}, base_delay={base_delay}, initial_cash={initial_cash}")
                    
    for model_config in enabled_models:
        # Read basemodel and signature directly from configuration file
        model_name = model_config.get("name", "unknown")
        signature = model_config.get("signature")

        # Validate signature (required for all agents)
        if not signature:
            print(f"❌ Model {model_name} missing signature field")
            continue

        print("=" * 60)
        print(f"🤖 Processing model: {model_name}")
        print(f"📝 Signature: {signature}")

        # Initialize runtime configuration
        write_config_value("SIGNATURE", signature)
        write_config_value("TODAY_DATE", END_DATE)
        write_config_value("IF_TRADE", False)

        # Get log path configuration
        log_path = log_config.get("log_path", "./data/agent_data")

        try:
            # Create Agent instance with appropriate parameters based on agent type
            if agent_type == "TraditionalAgent":
                # TraditionalAgent doesn't need AI model parameters
                strategy = model_config.get("strategy", "multi_indicator")
                max_position_pct = model_config.get("max_position_pct", 0.15)
                top_n_stocks = model_config.get("top_n_stocks", 10)

                print(f"📊 Strategy: {strategy}")
                print(f"💰 Max Position %: {max_position_pct * 100}%")
                print(f"🎯 Top N Stocks: {top_n_stocks}")

                agent = AgentClass(
                    signature=signature,
                    stock_symbols=all_nasdaq_100_symbols,
                    log_path=log_path,
                    initial_cash=initial_cash,
                    init_date=INIT_DATE,
                    max_position_pct=max_position_pct,
                    top_n_stocks=top_n_stocks,
                    strategy=strategy
                )
            elif agent_type == "MomentumAgent":
                # MomentumAgent - 动量策略代理
                lookback_period = model_config.get("lookback_period", 20)
                top_n_stocks = model_config.get("top_n_stocks", 10)
                momentum_threshold = model_config.get("momentum_threshold", 0.0)
                max_position_pct = model_config.get("max_position_pct", 0.15)
                stop_loss_pct = model_config.get("stop_loss_pct", 0.08)
                use_risk_management = model_config.get("use_risk_management", True)

                print(f"📊 Strategy: Momentum")
                print(f"📅 Lookback Period: {lookback_period} days")
                print(f"🎯 Top N Stocks: {top_n_stocks}")
                print(f"📈 Momentum Threshold: {momentum_threshold}")
                print(f"💰 Max Position %: {max_position_pct * 100}%")
                print(f"🛡️ Risk Management: {'Enabled' if use_risk_management else 'Disabled'}")

                agent = AgentClass(
                    signature=signature,
                    stock_symbols=all_nasdaq_100_symbols,
                    log_path=log_path,
                    initial_cash=initial_cash,
                    init_date=INIT_DATE,
                    lookback_period=lookback_period,
                    top_n_stocks=top_n_stocks,
                    momentum_threshold=momentum_threshold,
                    max_position_pct=max_position_pct,
                    stop_loss_pct=stop_loss_pct,
                    use_risk_management=use_risk_management
                )
            else:
                # BaseAgent and other AI-based agents
                basemodel = model_config.get("basemodel")
                openai_base_url = model_config.get("openai_base_url", None)
                openai_api_key = model_config.get("openai_api_key", None)

                # Validate required fields for AI agents
                if not basemodel:
                    print(f"❌ Model {model_name} missing basemodel field")
                    continue

                print(f"🔧 BaseModel: {basemodel}")

                agent = AgentClass(
                    signature=signature,
                    basemodel=basemodel,
                    stock_symbols=all_nasdaq_100_symbols,
                    log_path=log_path,
                    openai_base_url=openai_base_url,
                    openai_api_key=openai_api_key,
                    max_steps=max_steps,
                    max_retries=max_retries,
                    base_delay=base_delay,
                    initial_cash=initial_cash,
                    init_date=INIT_DATE
                )
            
            print(f"✅ {agent_type} instance created successfully: {agent}")
            
            # Initialize MCP connection and AI model
            await agent.initialize()
            print("✅ Initialization successful")
            # Run all trading days in date range
            await agent.run_date_range(INIT_DATE, END_DATE)
            
            # Display final position summary
            summary = agent.get_position_summary()
            print(f"📊 Final position summary:")
            print(f"   - Latest date: {summary.get('latest_date')}")
            print(f"   - Total records: {summary.get('total_records')}")
            print(f"   - Cash balance: ${summary.get('positions', {}).get('CASH', 0):.2f}")
            
        except Exception as e:
            print(f"❌ Error processing model {model_name} ({signature}): {str(e)}")
            print(f"📋 Error details: {e}")
            # Can choose to continue processing next model, or exit
            # continue  # Continue processing next model
            exit()  # Or exit program
        
        print("=" * 60)
        print(f"✅ Model {model_name} ({signature}) processing completed")
        print("=" * 60)
    
    print("🎉 All models processing completed!")
    
if __name__ == "__main__":
    import sys
    
    # Support specifying configuration file through command line arguments
    # Usage: python livebaseagent_config.py [config_path]
    # Example: python livebaseagent_config.py configs/my_config.json
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if config_path:
        print(f"📄 Using specified configuration file: {config_path}")
    else:
        print(f"📄 Using default configuration file: configs/default_config.json")
    
    asyncio.run(main(config_path))

