import Panel from './Panel'

interface Props{
    name: string,
    value: string
}
export default function InformationPanel({name, value}: Props) {
    return (
        <Panel styles='p-3 flex flex-col gap-2 min-w-30'>
            <p className='text-subtext2 text-sm'>
                {name}
            </p>
            <p className='text-title  text-3xl'>
                {value}
            </p>
        </Panel>
    )
}
