import { useEffect, useRef, useState, type ReactNode } from "react";
import { IoIosArrowDown } from "react-icons/io";
import React from "react";
import { Util } from "../../util/Util";

export interface dataFormat{
    icon?: ReactNode
    name: string,
    id: number
    data?: string | object
}

interface DropdownProps {
  items: dataFormat[];
  selectedItem: dataFormat | null;
  setSelectedItem: (id: number) => void;
  setText?: string | React.ReactNode
  defaultText?: string
  style?: string
  center?: boolean
  blur?: boolean
  showIcon?: boolean
  largeText?: boolean
  setBlur?: (blur: boolean) => void
  onBtnClick? : () => void
  onInnerClick?: () => void
  dropUp?: boolean
  divStyles?: string            
}
export default function Dropdown(props: DropdownProps) {
    const focusElement = useRef<null|HTMLDivElement>(null)
    const [clicked, setClicked] = useState(false)
    const [highlight, setHighlight] = useState(0)

    function setItem(id: number) {
        props.setSelectedItem(id);
        if(focusElement.current != null){
            setClicked(false)
            focusElement.current.blur()
        }
    }

    useEffect(() => {
        if(props.blur  && focusElement.current != null){
            setClicked(false)
            focusElement.current.blur()
        }
        const onClick = (e: MouseEvent) => {
            if (focusElement.current && !focusElement.current.contains(e.target as Node)) {
                setClicked(false);
            }
        }
        document.addEventListener("click", onClick)

        return () => {
            document.removeEventListener("click", onClick)
        }
    }, [props.blur])

    return (
        <div className={`relative ${props.divStyles}`} ref={focusElement}>
            <button
                type="button"
                aria-expanded={clicked}
                aria-haspopup="listbox"
                className={`whitespace-nowrap group text-xs relative transition-transform flex justify-between ${props.divStyles?.includes("bg-") ? "" : "bg-panel2"} items-center gap-1  hover:cursor-pointer ${props.style ? props.style : "w-full flex outline-1 px-3 h-7 rounded-md outline-border text-subtext3 "}`}
                onClick={(e) => {
                    setClicked(!clicked)
                    setHighlight(0)
                    props.onBtnClick?.()
                    e.stopPropagation()
                }}
                onKeyDown={event => {
                    if (event.key === "Escape") {
                        setClicked(false)
                        return
                    }
                    if (event.key === "ArrowDown") {
                        event.preventDefault()
                        if (!clicked) {
                            setClicked(true)
                            setHighlight(0)
                            return
                        }
                        setHighlight(index => Math.min(props.items.length - 1, index + 1))
                    }
                    if (event.key === "ArrowUp") {
                        event.preventDefault()
                        if (!clicked) return
                        setHighlight(index => Math.max(0, index - 1))
                    }
                    if ((event.key === "Enter" || event.key === " ") && clicked && props.items[highlight]) {
                        event.preventDefault()
                        props.onInnerClick?.()
                        setItem(props.items[highlight].id)
                    }
                }}>
                <p>
                    {props.setText 
                        ?? (props.selectedItem == null 
                        ? Util.capitilize(props.defaultText ?? "")
                        : Util.capitilize(props.selectedItem.name))} 
                </p>
                <p>
                    {props.showIcon ? <IoIosArrowDown className={`mt-0.5 transition-transform duration-300 ${
                        clicked? "rotate-180" : "rotate-0"
                    }`}/> : null}
                </p>
            </button>
            <div
                hidden={!clicked}
                role="listbox"
                className={`bg-panel2 absolute  mt-2 ${props.center ? "left-0" : "right-0 "} ${props.dropUp ? "bottom-full mb-2 mt-0" : ""} rounded-xl p-2.5  overflow-y-scroll no-scrollbar max-h-100 px-1.5 mb-1 ${props.largeText ? "gap-1.5" : "gap-1"} flex flex-col justify-start items-start bg-panel1 text-subtext1  outline-border2  z-20 w-fit outline-1`}
                onWheel={e => {
                    e.stopPropagation();
                    e.preventDefault();
                }}>
                {props.items && props.items.map((h, index) => {
                    return (
                    <button
                        type="button"
                        role="option"
                        aria-selected={index === highlight}
                        key={h.id}
                        className={`hover:bg-highlight transition-colors duration-200 ease-in-out gap-1.5 w-full flex items-center justify-start p-1 px-0.5 ${props.largeText ? "" : "text-sm"} rounded-lg hover:cursor-pointer text-nowrap hover:text-btn-text px-3 ${index === highlight ? "bg-highlight text-btn-text" : ""}`}
                        onMouseEnter={() => setHighlight(index)}
                        onClick={() => {
                            props.onInnerClick?.()
                            setItem(h.id)
                        }}>
                        {h.icon} {Util.capitilize(h.name)}
                    </button>
                    );
                })}
            </div>
        </div>
    );
}