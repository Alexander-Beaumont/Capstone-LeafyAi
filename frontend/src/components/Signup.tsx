import { AuthUtil } from "../util/Util";
import useForm from "./hooks/useFrom";
import Button from "./primatives/Button";
import TextBox from "./primatives/Textbox";
import { IoLogInOutline } from "react-icons/io5";
import ModalMessageBox from "./primatives/ModalMessageBox";
import Modal from "./primatives/Modal";
import { useContext } from "react";
import { userContext } from "../providers/UserProvider";

interface Props{
    setHasAccount: (hasAccount: boolean) => void
}
export default function Signup({setHasAccount}: Props) {
    const userData = useForm({email: "", password: "", confirmPassword: ""})
    const modalData = useForm({showModal: false, modalText: ""})
    const user = useContext(userContext)

    function singUp(){
        const [emailVal, emailRes] = AuthUtil.validateEmail(userData.form.email)
        const [passwordVal, passwordRes] = AuthUtil.validatePassword(userData.form.password, userData.form.confirmPassword)
        
        if(!emailVal || !passwordVal) {
            modalData.setWholeForm({showModal: true, modalText: emailRes + ", " + passwordRes})
            return
        }
        
    }

    function skip(){
        user.setLoggedIn(true)
    }

    return (
        <>
            <div className="bg-panel1 border border-border rounded-lg p-5 w-[80%] h-fit
                flex flex-col items-center max-w-80 gap-7 py-7 pb-9"
            >
                <p className="text-title font-semibold text-xl">
                    Sign Up
                </p>
                <div className="w-[90%] flex flex-col gap-4">
                    <TextBox
                        name="Email"
                        charLimit={30}
                        value={userData.form.email}
                        setValue={d => userData.setForm("email", d)}
                        placeHolder="Enter Email"
                    />
                    <TextBox
                        name="Password"
                        charLimit={15}
                        value={userData.form.password}
                        setValue={d => userData.setForm("password", d)}
                        placeHolder="Enter Email"
                        password={true}
                    />
                    <TextBox
                        name="Confirm Password"
                        charLimit={15}
                        value={userData.form.confirmPassword}
                        setValue={d => userData.setForm("confirmPassword", d)}
                        placeHolder="Enter Email"
                        password={true}
                    />
                    <div className="mt-3 flex flex-col items-center gap-5.5">
                        <Button
                            name="Sign Up"
                            highlight={true}
                            onSubmit={() => singUp()}
                            styles={{fullWidth: true}}
                            icon={<IoLogInOutline />}
                        />
                        <p className="text-xs text-subtext3">
                            {"Allready have an account? "}  
                            <span className="text-highlight underline hover:cursor-pointer"
                                onClick={() => setHasAccount(true)}>
                                {"Log In"}
                            </span>
                        </p>
                    </div>
                </div>
                <Button
                    name="Skip SignIn (Testing Purposes)"
                    highlight={true}
                    onSubmit={() => skip()}
                    styles={{fullWidth: false}}
                    icon={<IoLogInOutline />}
                />
            </div>
            <Modal open={modalData.form.showModal} onClose={() => modalData.setForm("showModal", false)}>
                <ModalMessageBox
                    title="Note"
                    text={modalData.form.modalText}
                    onClose={() => modalData.setForm("showModal", false)}
                />
            </Modal>
        </>
    )
}
