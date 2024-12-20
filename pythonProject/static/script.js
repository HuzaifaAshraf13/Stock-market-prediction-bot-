document.getElementById("send-button").addEventListener("click", async () => {
  const symbolInput = document.getElementById("symbol");
  const chatWindow = document.querySelector(".chat-window");

  // Get the coin pair entered by the user
  const coin = symbolInput.value.trim().toUpperCase();

  if (coin) {
    // Display user's request in the chat
    const userMessage = document.createElement("div");
    userMessage.className = "message user";
    userMessage.textContent = `Analyze ${coin}`;
    chatWindow.appendChild(userMessage);

    // Display bot's initial response
    const botMessage = document.createElement("div");
    botMessage.className = "message bot";
    botMessage.textContent = `Analyzing market data for ${coin}...`;
    chatWindow.appendChild(botMessage);

    // Scroll to the bottom of the chat window
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
      // Send the coin pair to the backend for analysis
      const response = await fetch('/analyze/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbol: coin }),
      });

      const data = await response.json();

      // Display the bot's final response based on the backend analysis
      if (response.ok) {
        botMessage.textContent = `Prediction for ${coin}: ${data.prediction}`;
      } else {
        botMessage.textContent = `Error: ${data.detail || 'Failed to analyze the data.'}`;
      }
    } catch (error) {
      console.error('Error:', error);
      botMessage.textContent = `Error: Unable to connect to the server.`;
    }
  } else {
    alert("Please enter a valid coin pair to analyze.");
  }

  // Clear the input field
  symbolInput.value = "";
});
