
var vm = new Vue({

    el: '#dashboard',

    data: {
        title: "Powered by Vue.js",
        tracker_card: {
            'title': '',
        },
        all_tracker_cards: []
    },

    async created() {
        await this.getTrackerCards()
    },

    methods: {

        async sendRequest(url, method, data) {
            const myHeaders = new Headers({
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            })

            const response = await fetch(url, {
                method: method,
                headers: myHeaders,
                body: data
            })

            return response
        },

        async getTrackerCards() {
            const response = await this.sendRequest(window.location.href, 'get')
            this.all_tracker_cards = await response.json()
        },

        async createTrackerCard() {
            await this.getTrackerCards()
            console.log(window.location.href + '/create')
            await this.sendRequest(window.location.origin + window.location.pathname + '/create' + window.location.search, 'post', JSON.stringify(this.tracker_card))
            await this.getTrackerCards()

            this.tracker_card.title = ''
        },

        async deleteTrackerCard(tracker_card) {

            await this.getTrackerCards()
            await this.sendRequest(window.location.origin + window.location.pathname + '/delete' + window.location.search, 'post', JSON.stringify(tracker_card))
            await this.getTrackerCards()
        }
    },

    delimiters: ['{', '}']
});