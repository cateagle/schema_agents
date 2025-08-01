# JSON Schema Search Agent

A powerful AI-driven research tool that helps you find and collect structured data using custom JSON schemas. Build schemas conversationally, then deploy specialized research agents to gather real-world data that matches your exact requirements.

## 🚀 Features

### 📋 **Schema Builder**
- **Conversational Schema Creation**: Chat with AI to build JSON schemas naturally
- **Real-time Validation**: Instant feedback and schema refinement
- **Template Library**: Pre-built schemas for common research tasks
- **Smart Extraction**: Automatic schema detection from conversations

### 🔍 **AI Research Orchestrator** 
- **Multi-Agent Research**: Deploy specialized agents for comprehensive data collection
- **Real-time Progress Tracking**: Watch your research unfold with detailed logging
- **Modern Chat Interface**: Clean, responsive UI with typing indicators and speech bubbles
- **Schema-Driven Results**: Agents find data that perfectly matches your schema structure

### 📊 **Data Management**
- **Schema Catalog**: Organize and reuse your schemas across projects
- **Multiple Export Formats**: JSON, CSV export options
- **Result Validation**: Automatic data validation against your schemas
- **Source Tracking**: Full provenance for all collected data

## 🛠 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get API Access**
   - Sign up at [OpenRouter](https://openrouter.ai) for LLM access
   - Add your API key in the app sidebar

3. **Launch the Application**
   ```bash
   streamlit run app.py
   ```

4. **Start Researching**
   - Create a schema describing your data needs
   - Chat with the research orchestrator to plan your approach
   - Execute multi-agent research and export results

## 📁 Project Structure

```
schema_agents/
├── app.py                    # Main Streamlit application
├── research_coordinator.py   # Multi-agent research orchestration
├── schemas/                  # Saved JSON schemas
├── agent_system/            # Core agent framework
│   ├── core/                # Base classes (Agent, Tool, Parser)
│   ├── agents/              # Specialized research agents
│   ├── tools/               # Research tools (web search, validation)
│   └── llm_apis/            # LLM provider integrations
├── streamlit_app/           # UI components and business logic
│   ├── components/          # Chat interfaces, schema builders
│   ├── config/              # Configuration and models
│   └── ui/                  # Reusable UI components
└── tests/                   # Comprehensive test suite
```

## 🎯 Use Cases

- **Market Research**: Find product specifications, pricing, availability
- **Academic Research**: Gather structured data from multiple sources
- **Competitive Analysis**: Collect competitor information systematically
- **Data Collection**: Build datasets for analysis or machine learning
- **Content Aggregation**: Gather structured content from various websites

## 🔧 Development

**Run Tests**
```bash
python -m pytest tests/ -v
```

**Check System Health**
```bash
python dev/check_agent_system_structure.py
```

## 🏗 Architecture

### **Modular Agent System**
- **Tool-based Architecture**: Extensible tools for different data sources
- **Dynamic Tool Management**: Runtime tool addition/removal with LLM notification
- **Schema Integration**: All tools understand and validate against your schemas

### **Research Coordination**
- **Parallel Agent Execution**: Multiple agents work simultaneously
- **Intelligent Task Distribution**: Smart workload balancing
- **Progress Monitoring**: Real-time visibility into research progress

## 🤖 How It Works

1. **Define Your Schema**: Use the conversational schema builder to describe exactly what data you need
2. **Plan Your Research**: Chat with the AI orchestrator to refine your research strategy
3. **Execute Multi-Agent Search**: Specialized agents search different sources simultaneously
4. **Collect Validated Results**: All data is automatically validated against your schema
5. **Export and Analyze**: Get clean, structured data ready for your analysis

## 📈 Built With

- **Streamlit**: Modern web app framework
- **OpenRouter**: Multi-provider LLM access
- **Pydantic**: Data validation and schema management
- **Requests**: Web scraping and API interactions
- **pytest**: Comprehensive testing framework


## Find Repo Here
https://github.com/cateagle/schema_agents