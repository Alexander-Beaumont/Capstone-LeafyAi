import { Route, Routes } from "react-router"
import LandingPage from "./pages/LandingPage"
import AuthPage from "./pages/AuthPage"
import Layout from "./pages/Layout"

function App() {
    return (
        <Routes>
            <Route element={<Layout/>}>
                <Route index element={<LandingPage/>}/>
                <Route path="auth" element={<AuthPage/>}/>
            </Route>
        </Routes>
    )
}
export default App
