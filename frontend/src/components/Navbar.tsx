import { Link, useLocation, useNavigate } from 'react-router'
import useSmallLayout from './hooks/useSmallLayout'
import { PAGE_NAMES, PAGES } from '../util/constants'
import Dropdown, { type dataFormat } from './primatives/Dropdown'
import { useContext, useState } from 'react'
import { userContext } from '../providers/UserProvider'
import { GiHamburgerMenu } from "react-icons/gi";
import { VscRobot } from "react-icons/vsc";
import { TbGrowth } from "react-icons/tb";
import { RiFolderHistoryLine } from "react-icons/ri";
import { LuHouse } from "react-icons/lu";
import { HiOutlineLogout } from "react-icons/hi";
import { GoGear } from 'react-icons/go'

export default function Navbar() {
    const smallLayout = useSmallLayout()
    const location = useLocation()
    const user = useContext(userContext)
    const navigate = useNavigate()

    const [selectedItem, setSelectedItem] = useState<dataFormat | null>(null)
    const items = [
        {id: 0, name: PAGE_NAMES.authPages.farmOverview, icon: <LuHouse />, data: PAGES.authPages.farmOverview},
        {id: 1, name: PAGE_NAMES.authPages.aiAgent, icon: <VscRobot size={16}/>, data: PAGES.authPages.aiAgent},
        {id: 2, name: PAGE_NAMES.authPages.growthHarvesting, icon: <TbGrowth size={16}/>, data: PAGES.authPages.growthHarvesting},
        {id: 3, name: PAGE_NAMES.authPages.history, icon:  <RiFolderHistoryLine />, data: PAGES.authPages.history},
        {id: 4, name: PAGE_NAMES.authPages.settings, icon:  <GoGear />, data: PAGES.authPages.settings},
        {id: 5, name: "Log Out", icon:   <HiOutlineLogout />, data: PAGES.noAuthPages.authPage}
    ]

    return (
        <>
            {smallLayout ? 
                <div className="top-0 left-0 z-10 border-b border-border fixed bg-panel1  w-full h-12 flex items-center justify-between">
                    <p className='text-lg font-semibold text-title px-3'>
                        Leafy<span className='text-highlight'>AI</span>
                    </p>
                    <div className='h-12'>
                        {!user.loggedIn ? 
                            <Link to="/auth" className='h-full'>
                                <button className="hover:cursor-pointer text-subtext1 h-full hover:bg-highlight hover:text-btn-text  text-xs transition-all duration-200 ease-in-out px-3">
                                    Sign Up
                                </button>
                            </Link> :
                            <Dropdown
                                items={items}
                                selectedItem={selectedItem}
                                setSelectedItem={(id) => {
                                    const item = items.find(i => i.id == id) ?? null
                                    if(item?.data == PAGES.noAuthPages.authPage) user.setLoggedIn(false)
                                    setSelectedItem(item)
                                    if(item?.name =="Log Out"){
                                        user.signout()
                                        return
                                    }
                                    navigate(item!.data)
                                }}
                                setText={<GiHamburgerMenu size={18}/>}
                                style='h-12 flex justify-center w-15 hover:cursor-pointer text-subtext1 hover:bg-highlight hover:text-btn-text  text-xs transition-all duration-200 ease-in-out px-3'
                            />
                        }
                    </div>
                </div>
            : 
                <div className="top-0 left-0 z-10 border-b border-border fixed bg-panel1 pl-1 w-50 h-full flex flex-col gap-10">
                    <p className='text-xl font-semibold text-title px-3 pt-5'>
                        Leafy<span className='text-highlight'>AI</span>
                    </p>
                    <div className='flex flex-col justify-between h-full mb-3'>
                        <div className='w-full flex flex-col gap-3'>
                            <Link to={PAGES.authPages.farmOverview} className=''>
                                <button className={`${location.pathname == PAGES.authPages.farmOverview ? "bg-highlight text-btn-text " : "text-subtext1 hover:bg-panel3 "} 
                                        hover:cursor-pointer text-sm h-10 hover:italic transition-all duration-200 ease-in-out px-3 w-full text-left
                                        flex items-center gap-2`}>
                                    <LuHouse />
                                    {PAGE_NAMES.authPages.farmOverview}
                                </button>
                            </Link>
                            <Link to={PAGES.authPages.aiAgent} className=''>
                                <button className={`${location.pathname == PAGES.authPages.aiAgent ? "bg-highlight text-btn-text " : "text-subtext1 hover:bg-panel3 "} 
                                        hover:cursor-pointer text-sm h-10 hover:italic transition-all duration-200 ease-in-out px-3 w-full text-left
                                        flex items-center gap-2`}>
                                    <VscRobot size={16}/>
                                    {PAGE_NAMES.authPages.aiAgent}
                                </button>
                            </Link>
                            <Link to={PAGES.authPages.growthHarvesting} className=''>
                                <button className={`${location.pathname == PAGES.authPages.growthHarvesting ? "bg-highlight text-btn-text " : "text-subtext1 hover:bg-panel3 "} 
                                        hover:cursor-pointer text-sm h-10 hover:italic transition-all duration-200 ease-in-out px-3 w-full text-left
                                        flex items-center gap-2`}>
                                    <TbGrowth size={16}/>
                                    {PAGE_NAMES.authPages.growthHarvesting}
                                </button>
                            </Link>
                            <Link to={PAGES.authPages.history} className=''>
                                <button className={`${location.pathname == PAGES.authPages.history ? "bg-highlight text-btn-text " : "text-subtext1 hover:bg-panel3 "} 
                                        hover:cursor-pointer text-sm h-10 hover:italic transition-all duration-200 ease-in-out px-3 w-full text-left
                                        flex items-center gap-2`}>
                                    <RiFolderHistoryLine />
                                    {PAGE_NAMES.authPages.history}
                                </button>
                            </Link>
                        </div>
                        <div>
                            <Link to={PAGES.authPages.settings} className=''>
                                <button className={`${location.pathname == PAGES.authPages.settings ? "bg-highlight text-btn-text " : "text-subtext1 hover:bg-panel3 "} 
                                        hover:cursor-pointer text-sm h-10 hover:italic transition-all duration-200 ease-in-out px-3 w-full text-left
                                        flex items-center gap-2`}>
                                    <GoGear />
                                    Settings
                                </button>
                            </Link>
                            <Link to={PAGES.noAuthPages.authPage} className=''>
                                <button className={`text-subtext1 hover:bg-panel3
                                        hover:cursor-pointer text-sm h-10 hover:italic transition-all duration-200 ease-in-out px-3 w-full text-left
                                        flex items-center gap-2`}
                                    onClick={() => user.signout()}>
                                    <HiOutlineLogout />
                                    Log Out
                                </button>
                            </Link>
                        </div>
                    </div>
                </div>
            }
        </>
    )
}
