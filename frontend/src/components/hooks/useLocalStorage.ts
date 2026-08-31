import { useCallback, useState } from "react";


export default function useLocalStorage(key: string, initialValue?: string) {
     const [value, setValue] = useState<string | undefined>(() => {
        if (typeof window === 'undefined') return initialValue 
        const item = localStorage.getItem(key)
        return item ?? initialValue
    })

    const setValueIntercept = useCallback((newValue: string) => {
        setValue(newValue)
        localStorage.setItem(key, newValue)
    }, [key])

    return [value, setValueIntercept] as const
}
