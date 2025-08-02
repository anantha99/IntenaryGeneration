# Travel Itinerary Generator

An AI-powered travel itinerary generator that creates personalized travel plans with activities, accommodations, and cost estimates.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- OpenRouter API key

### Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   
   Create a `.env` file in the project root:
   ```env
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

3. **Run the Application**
   ```bash
   venv/Scripts/python.exe src/cli/interactive_itinerary_generator.py
   ```

## 🎯 How to Use

1. **Start the Application**: Run the command above
2. **Describe Your Trip**: Tell the AI about your travel plans in natural language
   - Example: "I want to visit Paris for 5 days with 2 adults and 1 child, budget 5000 EUR"
3. **Answer Follow-up Questions**: The AI will ask clarifying questions to better understand your preferences
4. **Get Your Itinerary**: Receive a complete travel plan including:
   - Must-visit attractions and activities
   - Recommended accommodations with pricing
   - Cost estimates and budget breakdown
   - Day-by-day planning suggestions

## 📋 What You'll Get

The application generates a comprehensive travel itinerary including:

- **Destination Analysis**: Location details and travel type
- **Duration & Travelers**: Trip length and group composition
- **Activities & Attractions**: Must-visit places with categories and significance
- **Accommodations**: Hotel recommendations with pricing and proximity scores
- **Cost Estimates**: Budget breakdown and total trip costs
- **Performance Metrics**: Generation time and completion status

## 💾 Save Your Itinerary

After generation, you can save your itinerary to a text file for future reference.

## 🔧 Troubleshooting

- **API Key Issues**: Ensure your OpenRouter API key is correctly set in the `.env` file
- **Python Version**: Make sure you're using Python 3.12 or higher
- **Dependencies**: Run `pip install -r requirements.txt` if you encounter import errors

## 📞 Support

For technical support or questions about the application, please contact your development team.
