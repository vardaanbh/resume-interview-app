function submitResponses() {
    const loader = document.createElement('div');
    loader.className = 'loader';
    document.getElementById('interview-container').appendChild(loader);

    const responses = document.querySelectorAll('textarea');
    const userResponses = Array.from(responses).map(res => res.value);
    fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ responses: userResponses })
    })
    .then(response => response.json())
    .then(data => {
        loader.remove();
        alert('Feedback: ' + JSON.stringify(data));
    });
}