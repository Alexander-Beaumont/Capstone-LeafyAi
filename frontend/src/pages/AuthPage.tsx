import { useState } from "react";
import Signup from "../components/Signup";
import Login from "../components/Login";

export default function AuthPage() {
    const [hasAccount, setHasAccount] = useState(false)

    return (
        <div className="m-auto flex justify-center h-svh">
            {hasAccount ? 
                <Login setHasAccount={setHasAccount}/>:
                <Signup setHasAccount={setHasAccount}/>
            }
        </div>
    )
}
