import Panel from './Panel'

interface Props{
    name: string,
    value: string
}
export default function InformationPanel({name, value}: Props) {
    return (
        <Panel styles='p-3 flex flex-col gap-2 min-w-fit flex-1'>
            <p className='text-subtext2 text-sm'>
                {name}
            </p>
            <p className='text-highlight  text-3xl'>
                {value}
            </p>
        </Panel>
    )
}
