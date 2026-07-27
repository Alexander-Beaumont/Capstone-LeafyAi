import { Link, Outlet } from "react-router";
import Navbar from "../components/Navbar";

export default function Layout() {
    return (
        <div>
            <Navbar/>
            <main>
                <Outlet/>
            </main>
        </div>
    )
}
