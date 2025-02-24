
import axios, { AxiosError, CanceledError } from "axios"
import AWS from "./exports"

export { CanceledError, AxiosError }

export default (idToken: string) => {
    return axios.create({
        baseURL: AWS.API_ENDPOINT,
        headers: {
            Authorization: idToken
        }
    })
}
