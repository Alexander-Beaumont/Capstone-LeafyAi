import useForm from "./hooks/useFrom";
import Button from "./primatives/Button";
import TextBox from "./primatives/Textbox";
import { IoLogInOutline } from "react-icons/io5";
import { AuthUtil } from "../util/Util";
import Modal from "./primatives/Modal";
import ModalMessageBox from "./primatives/ModalMessageBox";

import { useContext } from "react";
import { userContext } from "../providers/UserProvider";

interface Props{
    setHasAccount: (hasAccount: boolean) => void
}
export default function Login({setHasAccount}: Props) {
    const userData = useForm({username: "", password: ""})
    const modalData = useForm({showModal: false, modalText: ""})
    const user = useContext(userContext)


    async function login() {
        const [passwordVal, passwordRes] =
           AuthUtil.validatePassword(userData.form.password)

        if(!passwordVal) {
            modalData.setWholeForm({
                showModal: true,
                modalText: passwordRes
            })
            return
        }

        const {loggedIn, msg} = await user.login(userData.form.username, userData.form.password)
        
        if(loggedIn) return
        
        modalData.setWholeForm({
            showModal: true,
            modalText: msg!
        })
    }
    return (
        <>
            <div className="bg-panel1 border border-border rounded-xl p-5 w-[80%] h-fit
                flex flex-col items-center max-w-80 gap-7 py-7 pb-9"
            >
                <p className="text-title font-semibold text-xl">
                    Log In
                </p>
                <div className="w-[90%] flex flex-col gap-4">
                    <TextBox
                        name="Username"
                        charLimit={30}
                        value={userData.form.username}
                        setValue={d => userData.setForm("username", d)}
                        placeHolder="Enter Username"
                    />
                    <TextBox
                        name="Password"
                        charLimit={15}
                        value={userData.form.password}
                        setValue={d => userData.setForm("password", d)}
                        placeHolder="Enter Password"
                        password={true}
                    />
                    <div className="mt-3 flex flex-col items-center gap-5.5">
                        <Button
                            name="Log In"
                            highlight={true}
                            onSubmit={() => login()}
                            styles={{fullWidth: true}}
                            icon={<IoLogInOutline />}
                            loading={user.loading}
                        />
                        <p className="text-xs text-subtext3">
                            {"Don't have an account? "}  
                            <span className="text-highlight underline hover:cursor-pointer"
                                onClick={() => setHasAccount(false)}>
                                {"Sign Up"}
                            </span>
                        </p>
                    </div>
                </div>
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
