import PageTitlePanel from "../components/primatives/PageTitlePanel"
import { GoGear } from "react-icons/go"

export default function Settings() {
    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="Settings"
                icon={ <GoGear />}
            />
        </div>
    )
}
