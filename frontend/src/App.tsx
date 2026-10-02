import { Navigate, Route, Routes } from "react-router"
import AuthPage from "./pages/AuthPage"
import Layout from "./pages/Layout"
import UserProvider from "./providers/UserProvider"
import FarmOverview from "./pages/FarmOverview"
import AiAgent from "./pages/AiAgent"
import GrowthHarvesting from "./pages/GrowthHarvesting"
import History from "./pages/History"
import Settings from "./pages/Settings"
import GrowthHarvestProvider from "./providers/GrowthHarvestProvider"
import FarmOverviewProvider from "./providers/FarmOverviewProvider"
import AiAgentProvider from "./providers/AiAgentProvider"

function App() {
    return (
        <UserProvider>
            <FarmOverviewProvider>
                <GrowthHarvestProvider>
                    <AiAgentProvider>
                        <Routes>
                            <Route element={<Layout/>}>
                                <Route index element={<Navigate to="/auth" replace />}/>
                                <Route path="auth" element={<AuthPage/>}/>
                                <Route path="farm-overview" element={<FarmOverview/>}/>
                                <Route path="ai-agent" element={<AiAgent/>}/>
                                <Route path="growth-harvesting" element={<GrowthHarvesting/>}/>
                                <Route path="history" element={<History/>}/>
                                <Route path="settings" element={<Settings/>}/>
                            </Route>
                        </Routes>
                    </AiAgentProvider>
                </GrowthHarvestProvider>
            </FarmOverviewProvider>
        </UserProvider>
    )
}
export default App
