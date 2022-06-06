const storage = window.localStorage;
const pufs = JSON.parse(storage.getItem('pufs'))
const order = JSON.parse(storage.getItem('order'))

function get_responses(challenges) {
    let responses = {}
    for (let i = 0; i < challenges.length; i++) {
        responses[challenges[i]] = challenge_response(challenges[i])
    }
    return responses
}

function challenge_response(challenge_vector) {
    let response = '';
    for(let i = 0; i < order.length; i++) {
        response += challenge(pufs[order[i]-1], challenge_vector)
    }
    return response
}

function challenge(puf, challenge_vector) {
    let features = []
    for(let i = 0; i < puf.length; i++) {
        let f = 1
        for(let j = i; j < puf.length; j++) {
            f *= (-1) ** challenge_vector[j]
        }
        features.push(f)
    }
    features.push(1)
    return dot(puf, features) > 0 ? 1 : 0
}

dot = (a, b) => a.map((x, i) => a[i] * b[i]).reduce((m, n) => m + n);