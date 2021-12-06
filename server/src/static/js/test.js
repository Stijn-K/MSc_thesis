let elem = document.createElement('h2');
elem.innerText = 'test';
document.body.appendChild(elem);

fetch('https://localhost:5000/alive').then(
    function(response) {
        document.body.innerHTML += response.status;
    }).catch(function (err) {
        document.body.innerHTML += err;
    })