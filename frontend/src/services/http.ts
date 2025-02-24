
import { AxiosInstance } from "axios"
import ApiGateway from "./client"

export class HttpService {
    endpoint: string
    idToken: string
    apiClient: AxiosInstance

    constructor(endpoint: string, idToken: string) {
        this.endpoint = endpoint
        this.idToken = idToken
        this.apiClient = ApiGateway(this.idToken)
    }

    getAll<T>() {
        const controller = new AbortController()
        const request = this.apiClient.get<T[]>(this.endpoint, { signal: controller.signal })

        return { request, cancel: () => controller.abort() }
    }

    delete<T>(entity: T) {
        return this.apiClient.delete(this.endpoint + "/", { data: { source: entity } })
    }

    post<T>(entity: T) {
        return this.apiClient.post(this.endpoint + "/", entity)
    }
}

const create = (endpoint: string, idToken: string) => {
    return new HttpService(endpoint, idToken)
}

export default create
