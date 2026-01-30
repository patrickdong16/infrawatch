'use client';

import { useState, ReactNode } from 'react';
import { HelpCircle } from 'lucide-react';

interface TooltipProps {
    content: string;
    children?: ReactNode;
}

export default function MetricTooltip({ content, children }: TooltipProps) {
    const [show, setShow] = useState(false);

    return (
        <span
            className="relative inline-flex items-center gap-1 cursor-help"
            onMouseEnter={() => setShow(true)}
            onMouseLeave={() => setShow(false)}
        >
            {children}
            <HelpCircle className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />

            {show && (
                <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 
                        bg-gray-900 text-white text-xs rounded-lg shadow-lg
                        whitespace-normal w-64 text-left font-normal">
                    {content}
                    <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></span>
                </span>
            )}
        </span>
    );
}
