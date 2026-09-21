import { RiFolderHistoryLine } from "react-icons/ri";
import AIDecisionsPanel from "../components/history-components/AIDecisionsPanel";
import PageTitlePanel from "../components/primatives/PageTitlePanel";

export default function History() {

    return (
        <div className="flex flex-col w-full items-center p-5 max-w-250 m-auto gap-5">
            <PageTitlePanel
                title="History"
                icon={ <RiFolderHistoryLine />}
            />
            <AIDecisionsPanel/>
        </div>
    )
}
