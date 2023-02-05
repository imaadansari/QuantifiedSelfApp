
var vm = new Vue({

    el: '#home',

    data: {
        title: "Powered by Vue.js",
        tracker_instance: {
            'value': '',
            'note': ''
        },
        tracker_instances: []
    },

    async created() {
        await this.getTrackerInstance()
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

        async getTrackerInstance() {
            const response = await this.sendRequest(window.location.href, 'get')
            this.tracker_instances = await response.json()
        },

        async createTrackerInstance() {
            await this.getTrackerInstance()
            await this.sendRequest(window.location.origin + window.location.pathname + '/create' + window.location.search, 'post', JSON.stringify(this.tracker_instance))
            await this.getTrackerInstance()

            this.tracker_instance.note = ''
            this.tracker_instance.value = ''
        },

        async deleteTrackerInstance(tracker_instance) {
            console.log(this.to_delete)
            await this.getTrackerInstance()
            await this.sendRequest(window.location.origin + window.location.pathname + '/delete' + window.location.search, 'post', JSON.stringify(tracker_instance))
            await this.getTrackerInstance()
        }
    },

    delimiters: ['{', '}']
});