const BACKEND_URL = "http://localhost:5000";

function handleKeyPress(event) {
  if (event.key === "Enter") {
    generateMCQ();
  }
}

async function generateMCQ() {
  const topicInput = document.getElementById("topic");
  const topic = topicInput.value.trim();
  const container = document.getElementById("mcqContainer");
  const btn = document.getElementById("generateBtn");
  const btnText = document.getElementById("btnText");
  const loader = document.getElementById("loader");

  if (!topic) {
    topicInput.focus();
    return;
  }

  // Set loading state
  btn.disabled = true;
  btnText.textContent = "Generating...";
  loader.style.display = "block";
  container.innerHTML = "";

  try {
    const response = await fetch(`${BACKEND_URL}/generate-mcqs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ topic })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to generate MCQs");
    }

    if (data.mcqs && Array.isArray(data.mcqs)) {
      renderMCQs(data.mcqs, container);
    } else if (data.raw_text) {
      // Fallback if AI didn't output proper JSON
      container.innerHTML = `
        <div class="mcq-card">
          <p style="color: #cbd5e1; margin-bottom: 12px;">The AI model returned unstructured text:</p>
          <pre style="white-space: pre-wrap; font-family: monospace; background: rgba(0,0,0,0.3); padding: 16px; border-radius: 8px;">${data.raw_text}</pre>
        </div>
      `;
    } else {
      throw new Error("Unexpected response format from server");
    }

  } catch (error) {
    console.error("Error generating MCQs:", error);
    container.innerHTML = `<div class="raw-error"><strong>Error:</strong> ${error.message}</div>`;
  } finally {
    // Reset loading state
    btn.disabled = false;
    btnText.textContent = "Generate MCQs";
    loader.style.display = "none";
  }
}

function renderMCQs(mcqs, container) {
  mcqs.forEach((mcq, index) => {
    // Ensure data is somewhat valid
    if (!mcq.question || !Array.isArray(mcq.options)) return;

    const card = document.createElement('div');
    card.className = 'mcq-card';
    
    // Add Question
    const questionEl = document.createElement('div');
    questionEl.className = 'mcq-question';
    questionEl.textContent = `${index + 1}. ${mcq.question}`;
    card.appendChild(questionEl);

    // Add Options container
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'mcq-options';

    mcq.options.forEach((option, optIdx) => {
      const label = document.createElement('label');
      label.className = 'option-label';
      
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = `question_${index}`;
      radio.value = option;
      
      const textNode = document.createTextNode(option);
      
      label.appendChild(radio);
      label.appendChild(textNode);
      optionsContainer.appendChild(label);

      // Handle selection change to give immediate feedback
      radio.addEventListener('change', () => {
        const feedbackEl = card.querySelector('.answer-feedback');
        if (radio.checked) {
          feedbackEl.style.display = 'block';
          if (option === mcq.answer) {
            feedbackEl.textContent = 'Correct!';
            feedbackEl.className = 'answer-feedback feedback-correct';
          } else {
            feedbackEl.textContent = `Incorrect. The correct answer is: ${mcq.answer}`;
            feedbackEl.className = 'answer-feedback feedback-incorrect';
          }
        }
      });
    });

    card.appendChild(optionsContainer);

    // Add Feedback element
    const feedbackEl = document.createElement('div');
    feedbackEl.className = 'answer-feedback';
    card.appendChild(feedbackEl);

    container.appendChild(card);
  });
}