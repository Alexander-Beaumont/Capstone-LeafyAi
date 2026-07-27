import { Link } from 'react-router'

export default function Navbar() {
    return (
        <div className="top-0 left-0 z-10 border-b border-border fixed bg-panel1  w-full h-12 flex items-center justify-between">
            <p className='text-lg font-semibold text-title px-3'>
                Leafy<span className='text-highlight'>AI</span>
            </p>
            <div className='h-full'>
                <Link to="/auth" className='h-full'>
                    <button className="hover:cursor-pointer text-subtext1 h-full hover:bg-highlight hover:text-btn-text  text-xs transition-all duration-200 ease-in-out px-3">
                        Sign Up
                    </button>
                </Link>
            </div>
        </div>
    )
}
