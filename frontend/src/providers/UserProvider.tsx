import React, { createContext, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { API, PAGES } from "../util/constants";
import useLocalStorage from "../components/hooks/useLocalStorage";

interface AuthResult {
    loggedIn: boolean
    accessToken?: string
    msg?: string 
}

export interface UserType {
    loggedIn: boolean;
    setLoggedIn: (loggedIn: boolean) => void;

    accessToken: string | undefined;
    setAccessToken: (accessToken: string) => void;
    
    refreshToken: string | undefined; //Alex
    setRefreshToken: (refreshToken: string) => void; //Alex
    
    id: string | null;
    setId: (id: string) => void;
    
    email: string | null;
    setEmail: (email: string) => void;
    
    getValidAccessToken: (refreshToken: string) => Promise<AuthResult> | AuthResult

    login: (username: string, password: string) => Promise<AuthResult>;
    
    timeAccesTokenCreated: number | null;
    
    loading: boolean
    setLoading: (loading: boolean) => void
}

const initialUserValues: UserType = {
    loggedIn: false,
    setLoggedIn: () => null,
    
    accessToken: undefined,
    setAccessToken: () => null,
    
    refreshToken: undefined, //Alex
    setRefreshToken: () => null, //Alex

    id: null,
    setId: () => null,
    
    email: null,
    setEmail: () => null,
    
    loading: false,
    setLoading: () => null,

    getValidAccessToken: () => Promise.resolve({loggedIn: false, accessToken: ""}),
    
    login: () => Promise.resolve({loggedIn: false, accessToken: ""}),
    
    timeAccesTokenCreated: null,
};

export const userContext = createContext<UserType>(initialUserValues);

interface Props {
    children: React.ReactNode;
}
export default function UserProvider(props: Props) {
    const [loggedIn, setLoggedIn] = useState(initialUserValues.loggedIn);
    const [accessToken, setAccessToken] = useLocalStorage("accessToken", initialUserValues.accessToken ?? undefined);

    const [refreshToken, setRefreshToken] = useLocalStorage("refreshToken", initialUserValues.refreshToken ?? undefined); //Alex
    const [id, setId] = useState(initialUserValues.id); 
    
    const [email, setEmail] = useState(initialUserValues.email);
    const [loading, setLoading] = useState(false)
    
    const [timeAccesTokenCreated, setTimeAccesTokenCreated] = useState(initialUserValues.timeAccesTokenCreated);
    
    const location = useLocation()
    const navigate = useNavigate()
    
    const AccesTokenRefreshTime = 10 * 60 * 1000;

    useEffect(() => {
        if(Object.values(PAGES.noAuthPages).includes(location.pathname) && loggedIn){
            navigate("/farm-overview")
        }
        if(Object.values(PAGES.authPages).includes(location.pathname) && !loggedIn){
            navigate("/auth")
        }

    }, [loggedIn, location.pathname])

    function isAccessTokenStillValid(){
        if (timeAccesTokenCreated == null || !accessToken) return false
        return Date.now() - timeAccesTokenCreated <= AccesTokenRefreshTime
    }

    async function getValidAccessToken(refreshToken: string): Promise<AuthResult> { 
        if(isAccessTokenStillValid())  return { loggedIn: true, accessToken: accessToken ?? ""};

        try {
            const res = await fetch(API.refresh, { 
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ refresh: refreshToken }), 
            });
            
            if(!res.ok) {
                setNotLoggedInState()
                return { loggedIn: false, accessToken: "" };
            }
            
            const data = await res.json();
            setAuthenticatedState(data.access)

            return { loggedIn: true, accessToken: data.access }; 
        } catch (error) {
            setNotLoggedInState()
            return { loggedIn: false, accessToken: "" };
        }
    }

    async function login(username: string, password: string): Promise<AuthResult>{
        try {
            const response = await fetch(
                API.login,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password,
                    }),
                }
            )

            if(!response.ok){
                return {loggedIn: false, msg: "Invalid username or password"}
            }

            const data = await response.json()
            setRefreshToken(data.refresh)
            setAuthenticatedState(data.access)
            return {loggedIn: true}

        } catch(error) {
            return {loggedIn: false, msg: "Could not connect to backend"}
        }
    }

    async function signup(){
        
    }

    function setAuthenticatedState(newAccessToken: string) {
        setAccessToken(newAccessToken)
        setLoggedIn(true)
        setTimeAccesTokenCreated(Date.now())
    }

    function setNotLoggedInState(){
        setLoggedIn(false)
        setAccessToken("")
        setRefreshToken("")
        setTimeAccesTokenCreated(null)
    }
    return (
        <userContext.Provider
        value={{
            loggedIn: loggedIn,
            setLoggedIn: setLoggedIn,
            accessToken: accessToken,
            setAccessToken: setAccessToken,

            refreshToken: refreshToken, //Alex
            setRefreshToken: setRefreshToken, //Alex

            id: id,
            setId: setId,

            email: email,
            setEmail: setEmail,

            getValidAccessToken: getValidAccessToken,

            login: login,

            timeAccesTokenCreated: timeAccesTokenCreated,

            loading: loading,
            setLoading: setLoading
        }}>
        {props.children}
        </userContext.Provider>
    );
}