let mediaRecorder;
let audioChunks = [];
let isRecording = false;

document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const recordBtn = document.getElementById('record-btn');
    const setupSection = document.querySelector('.setup-section');
    const conversationSection = document.querySelector('.conversation-section');

    startBtn.addEventListener('click', () => {
        const level = document.getElementById('level-select').value;
        const topic = document.getElementById('topic-select').value;
        
        setupSection.style.display = 'none';
        conversationSection.style.display = 'block';
        
        startConversation(level, topic);
    });

    recordBtn.addEventListener('mousedown', startRecording);
    recordBtn.addEventListener('mouseup', stopRecording);
    recordBtn.addEventListener('mouseleave', stopRecording);

    // Request microphone permission
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const level = document.getElementById('level-select').value;
                await processAudio(audioBlob, level);
                audioChunks = [];
            };
        });
});

async function startConversation(level, topic) {
    try {
        const response = await fetch('/start_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ level, topic })
        });
        
        const data = await response.json();
        displayMessage(data.response, 'assistant');
        displaySuggestions(data.suggestions);
    } catch (error) {
        console.error('Error:', error);
    }
}

function startRecording() {
    if (mediaRecorder && !isRecording) {
        mediaRecorder.start();
        isRecording = true;
        document.getElementById('record-btn').classList.add('recording');
        document.getElementById('record-btn').textContent = 'Recording...';
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById('record-btn').classList.remove('recording');
        document.getElementById('record-btn').textContent = 'Hold to Speak';
    }
}

async function processAudio(audioBlob, level) {
    // In a real implementation, you would:
    // 1. Convert the audio to text using Google Speech-to-Text
    // 2. Send the text to your backend
    // For now, we'll simulate this with a text input
    
    const text = await simulateSTT(audioBlob);
    displayMessage(text, 'user');

    try {
        const response = await fetch('/process_speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                audio: text,
                level: level
            })
        });
        
        const data = await response.json();
        displayMessage(data.response, 'assistant');
        displaySuggestions(data.suggestions);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayMessage(message, role) {
    const chatContainer = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function displaySuggestions(suggestions) {
    const suggestionsDiv = document.getElementById('suggestions');
    suggestionsDiv.innerHTML = `<h3>Suggested Responses:</h3>${suggestions}`;
}

// Temporary function to simulate Speech-to-Text
async function simulateSTT(audioBlob) {
    // In a real implementation, you would send the audio to Google Speech-to-Text
    // For now, we'll simulate with a prompt
    return prompt("What did you say? (Simulating Speech-to-Text)");
} 