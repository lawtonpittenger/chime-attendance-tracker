
import create from "./http"

export interface Schedule {
    Name: string,
    Description: string,
    ScheduleExpression: string
}

export default (endpoint: string, idToken: string) => {
    if (idToken.length === 0)
        return
    return create(endpoint, idToken)
}
