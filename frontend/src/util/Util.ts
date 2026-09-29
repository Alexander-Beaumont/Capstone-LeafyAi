export namespace Util{
    export function setValueLim(setFunc: (value: string) => void, value: string, lim: number){
        if(value.length <= lim){
            setFunc(value)
        }
    }

    export function capitilize(string: string){
        if(!string) return ""
        return [string.split("")[0].toUpperCase(), ...string.split("").slice(1)].join("")
    }

    export function formatDate(date: Date){
        return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`
    }

    export function formatDateTime(date: Date){
        return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()} ${date.getHours()}:${date.getMinutes()}`
    }

    export function avgAge(dates: Date[]){
        const today = Date.now()
        const dateSum = dates.reduce((a, c) => a + (today - c.getTime()), 0)

        return dateSum/dates.length
    }

    export function millisecondsToDays(milliseconds: number, roundTo: number){
        const multiplier = Number("1".padEnd(roundTo+1, "0"))
        return Math.round(milliseconds/1000/60/60/24*multiplier)/multiplier
    }
}


export namespace AuthUtil{
    export function validateUsername(email: string): [boolean, string]{
        if(email.length == 0){
            return [false, "Enter an username"]
        }
        return [true, ""]
    }

    const CAPITAL_LETTER_REGEX = /[A-Z]/;
    const NUMBER_REGEX = /\d/;
    const SPECIAL_CHARACTER_REGEX = /[^a-zA-Z0-9]/;

    export function validatePassword(password: string, confirmationPassword?: string): [boolean, string]{
        if(password != confirmationPassword && confirmationPassword){
            return [false, "Passwords do not match"]
        }
        if(password.length < 6){
            return [false, "Password too short"]
        }
        if(!CAPITAL_LETTER_REGEX.test(password)){
            return [false, "Password needs atleast one capital letter"]
        }
        if(!NUMBER_REGEX.test(password)){
            return [false, "Password needs atleast one number"]
        }
        if(!SPECIAL_CHARACTER_REGEX.test(password)){
            return [false, "Password needs atleast one special character"]
        }
        return [true, ""]
    }
}