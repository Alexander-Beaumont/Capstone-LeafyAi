import { useContext } from "react"
import { useWindowWidth } from "./useWindowWidth"
import { userContext } from "../../providers/UserProvider"
import { SMALL_WINDOW_WIDTH } from "../../util/constants"


export default function useSmallLayout() {
    const width = useWindowWidth()
    const user = useContext(userContext)

    return width < SMALL_WINDOW_WIDTH|| !user.loggedIn
}
