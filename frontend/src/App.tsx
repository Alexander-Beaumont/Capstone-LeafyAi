import { Route, Routes } from "react-router"
import LandingPage from "./pages/LandingPage"
import AuthPage from "./pages/AuthPage"
import Layout from "./pages/Layout"
import UserProvider from "./providers/UserProvider"
import FarmOverview from "./pages/FarmOverview"
import PlantVision from "./pages/PlantVision"
import AiAgent from "./pages/AiAgent"
import GrowthHarvesting from "./pages/GrowthHarvesting"
import History from "./pages/History"
import Settings from "./pages/Settings"
import GrowthHarvestProvider from "./providers/GrowthHarvestProvider"
import FarmOverviewProvider from "./providers/FarmOverviewProvider"

function App() {
    return (
        <UserProvider>
            <GrowthHarvestProvider>
                <FarmOverviewProvider>
                    <Routes>
                        <Route element={<Layout/>}>
                            <Route index element={<LandingPage/>}/>
                            <Route path="auth" element={<AuthPage/>}/>
                            <Route path="farm-overview" element={<FarmOverview/>}/>
                            <Route path="plant-vision" element={<PlantVision/>}/>
                            <Route path="ai-agent" element={<AiAgent/>}/>
                            <Route path="growth-harvesting" element={<GrowthHarvesting/>}/>
                            <Route path="history" element={<History/>}/>
                            <Route path="settings" element={<Settings/>}/>
                        </Route>
                    </Routes>
                </FarmOverviewProvider>
            </GrowthHarvestProvider>
        </UserProvider>
    )
}
export default App
