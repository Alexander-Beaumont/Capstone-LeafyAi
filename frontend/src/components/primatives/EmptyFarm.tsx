import { Link } from "react-router"
import { PAGES } from "../../util/constants"

interface Props {
    noFarms: boolean
    onSettings?: boolean
}

export default function EmptyFarm({ noFarms, onSettings }: Props) {
    if (noFarms && onSettings) {
        return <p className="w-full text-sm text-subtext3">No farms yet. Create one with the form below.</p>
    }
    if (noFarms) {
        return (
            <p className="w-full text-sm text-subtext3">
                No farms yet.{" "}
                <Link to={PAGES.authPages.settings} className="text-highlight hover:underline">
                    Create a farm in Settings.
                </Link>
            </p>
        )
    }
    return <p className="w-full text-sm text-subtext3">Select a farm in the navigation bar.</p>
}
