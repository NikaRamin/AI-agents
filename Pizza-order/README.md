# 🍕 PizzaBot - AI-Powered Pizza Ordering System

An interactive pizza ordering chatbot built with Gradio and Google's Gemini AI. Experience natural conversations while ordering your favorite pizzas!

## ✨ Features

- 🤖 Natural language ordering process
- 🧠 Smart order customization
- 🔄 Interactive confirmation system
- 💾 Order state management
- 🖼️ Clean web interface
- 📋 Dynamic menu system
- 💰 Automatic price calculation

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd gradio_test
```

2. Install dependencies:
```bash
pip install langchain-google-genai python-dotenv gradio langgraph
```

3. Set up your environment:
   - Create a `.env` file in the project root
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

4. Run the application:
```bash
python main.py
```

## 🛠️ Technical Stack

- **Frontend**: Gradio
- **Backend**: Python with LangChain
- **AI Model**: Google Gemini 2.0 Flash
- **State Management**: Custom TypedDict implementation

## 🍽️ Menu Options

### Pizza Base Prices
- Small (10"): $10
- Medium (12"): $12
- Large (14"): $15
- Extra Large (16"): $18

### Specialty Pizzas
- 🧀 Margherita
- 🍖 Pepperoni
- 🍍 Hawaiian
- 🥬 Vegetarian
- 🎯 Supreme (+$2)

### Customization
- Extra Toppings: +$1.50 each
- Crust Options:
  - Regular/Thin: Included
  - Thick: +$1
  - Stuffed: +$2

## 💬 Example Conversation

```
Bot: Welcome! What kind of pizza can I get started for you today?
You: I'd like a large pepperoni pizza
Bot: Would you like any extra toppings with that?
You: Yes, extra cheese please
Bot: I'll add a large pepperoni pizza with extra cheese. Would you like to confirm your order?
You: Yes
Bot: Great! Your order will be ready for pickup in 20-30 minutes.
```

## 🤝 Contributing

Feel free to fork, create issues, or submit PRs. All contributions are welcome!

## 📝 License

MIT License - feel free to use this project for learning or building your own chatbot!

## 🙏 Acknowledgments

- Built with Google's Gemini AI
- Powered by LangChain and Gradio
- Inspired by real-world pizza ordering systems

