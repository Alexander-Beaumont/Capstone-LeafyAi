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
}


export namespace AuthUtil{
    export function validateEmail(email: string): [boolean, string]{
        if(email.length == 0){
            return [false, "Enter an email"]
        }
        if(!email.includes("@")){
            return [false, "Email needs to include an @"]
        }
        if(!email.includes(".")){
            return [false, "Email needs to include a '.'"]
        }
        return [true, ""]
    }

    const CAPITAL_LETTER_REGEX = /[A-Z]/;
    const NUMBER_REGEX = /\d/;
    const SPECIAL_CHARACTER_REGEX = /[^a-zA-Z0-9]/;

    export function validatePassword(password: string, confirmationPassword?: string): [boolean, string]{
        if(password != confirmationPassword){
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