import { useState, useEffect } from 'react';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

type RelativeTimeProps = {
    readonly iso: string;
};

export default function RelativeTime({ iso }: RelativeTimeProps) {
    const [relative, setRelative] = useState(dayjs(iso).fromNow());
    const formattedDate = dayjs(iso).format('MM/DD/YY HH:mm:ss');

    useEffect(() => {
        const intervalId = setInterval(() => {
            setRelative(dayjs(iso).fromNow());
        }, 4000); // update every 4 seconds

        return () => clearInterval(intervalId);
    }, [iso]);

    return <span title={formattedDate}>{relative}</span>;
}