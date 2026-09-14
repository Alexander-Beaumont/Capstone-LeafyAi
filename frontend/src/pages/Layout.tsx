import { Outlet } from "react-router";
import Navbar from "../components/Navbar";
import useSmallLayout from "../components/hooks/useSmallLayout";

export default function Layout() {
    const smallLayout = useSmallLayout()
    const offset = smallLayout ? "mt-15" : "ml-50 mt-5"

    return (
        <div>
            <Navbar/>
            <main className={`${offset}`}>
                <Outlet/>
            </main>
        </div>
    )
}
