document.addEventListener('DOMContentLoaded', async function() {
    let data = {
        audio: await audioFingerprint(),
        canvas: canvasFingerprint(),
    }

    fetch('https://localhost:5000/test', {
        method: 'POST',
        body: JSON.stringify(data)
    })

    let elem = document.createElement('h2');
    elem.innerText = 'test';
    document.body.appendChild(elem);

})


async function audioFingerprint() {
    // taken from https://fingerprintjs.com/blog/audio-fingerprinting/
    let context = new window.OfflineAudioContext(1, 5000, 44100);

    let oscillator = context.createOscillator();
    oscillator.type = 'triangle';
    oscillator.frequency.value = 1000;

    let compressor = context.createDynamicsCompressor();
    compressor.threshold.value = -50;
    compressor.knee.value = 40;
    compressor.ratio.value = 12;
    compressor.reduction.value = 20;
    compressor.attack.value = 0;
    compressor.release.value = 0.2;

    oscillator.connect(compressor);
    compressor.connect(context.destination);

    oscillator.start();

    let hash = await context.startRendering().then(function(renderedBuffer) {
        let samples = renderedBuffer.getChannelData(0);
        let hash = 0;
        for (let i = 0; i < samples.length; ++i) {
            hash += Math.abs(samples[i]);
        }
        return hash;
    });
    return hash
}

function canvasFingerprint() {
    // taken from https://fingerprintjs.com/blog/canvas-fingerprinting/
    let canvas = document.createElement('canvas');
    canvas.height = 200;
    canvas.width = 500;
    let ctx = canvas.getContext('2d');

    let txt = "❁ This Is A String with Emoji's!\n\r <🍏🍎🍐🍊🍋🍌🍉🍇🍓🍈🍒🍑🍍🥝>";
    ctx.textBaseline = "top";
    // The most common type
    ctx.font = "14px 'Arial'";
    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#f60";
    ctx.fillRect(125,1,62,20);
    // Some tricks for color mixing to increase the difference in rendering
    ctx.fillStyle = "#069";
    ctx.fillText(txt, 2, 15);
    ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
    ctx.fillText(txt, 4, 17);

    ctx.globalCompositeOperation = "multiply";
    ctx.fillStyle = "rgb(255,0,255)";
    ctx.beginPath();
    ctx.arc(50, 50, 50, 0, Math.PI * 2, true);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "rgb(0,255,255)";
    ctx.beginPath();
    ctx.arc(100, 50, 50, 0, Math.PI * 2, true);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "rgb(255,255,0)";
    ctx.beginPath();
    ctx.arc(75, 100, 50, 0, Math.PI * 2, true);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "rgb(255,0,255)";

    ctx.arc(75, 75, 75, 0, Math.PI * 2, true);
    ctx.arc(75, 75, 25, 0, Math.PI * 2, true);
    ctx.fill("evenodd");

    // hashing function
    let src = canvas.toDataURL();
    let hash = 0;

    for (i = 0; i < src.length; i++) {
        let char = src.charCodeAt(i);
        hash = ((hash<<5)-hash)+char;
        hash = hash & hash;
    }
    return hash;
}
