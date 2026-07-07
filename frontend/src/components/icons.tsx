import * as React from "react";

type IconProps = {
  size?: number;
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
};

const Icon: React.FC<IconProps & { children: React.ReactNode }> = ({
  size = 20, fill = "none", stroke = "currentColor", strokeWidth = 1.6, children,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke={stroke}
       strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

const path = (d: string) => (p: IconProps) => (<Icon {...p}><path d={d} /></Icon>);

export const Icons = {
  home: path("M3 11l9-8 9 8M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"),
  calendar: (p: IconProps) => (<Icon {...p}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></Icon>),
  list: path("M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"),
  users: (p: IconProps) => (<Icon {...p}><circle cx="9" cy="8" r="3.5"/><path d="M2 21c0-3.5 3.1-6 7-6s7 2.5 7 6"/><circle cx="17" cy="9" r="2.5"/><path d="M22 19c0-2.5-2-4.5-5-4.5"/></Icon>),
  user: (p: IconProps) => (<Icon {...p}><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.5-7 8-7s8 3 8 7"/></Icon>),
  scissors: (p: IconProps) => (<Icon {...p}><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4L8.5 15.5M14.5 12.5L20 18M8.5 8.5L11 11"/></Icon>),
  clock: (p: IconProps) => (<Icon {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></Icon>),
  message: path("M21 15a3 3 0 0 1-3 3H8l-5 4V6a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3z"),
  bell: (p: IconProps) => (<Icon {...p}><path d="M18 16V11a6 6 0 0 0-12 0v5l-2 2v1h16v-1z"/><path d="M10 21a2 2 0 0 0 4 0"/></Icon>),
  settings: (p: IconProps) => (<Icon {...p}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></Icon>),
  plus: path("M12 5v14M5 12h14"),
  search: (p: IconProps) => (<Icon {...p}><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></Icon>),
  check: path("M5 12.5l4.5 4.5L20 6.5"),
  x: path("M6 6l12 12M18 6L6 18"),
  chevronLeft: path("M15 6l-6 6 6 6"),
  chevronRight: path("M9 6l6 6-6 6"),
  chevronDown: path("M6 9l6 6 6-6"),
  menu: path("M4 6h16M4 12h16M4 18h16"),
  more: (p: IconProps) => (<Icon {...p}><circle cx="12" cy="6" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="18" r="1"/></Icon>),
  phone: path("M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"),
  mail: (p: IconProps) => (<Icon {...p}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></Icon>),
  edit: path("M4 20h4L20 8l-4-4L4 16v4zM14 6l4 4"),
  trash: (p: IconProps) => (<Icon {...p}><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></Icon>),
  whatsapp: path("M20 12a8 8 0 1 1-3.4-6.5L20 4l-1.3 3.6A8 8 0 0 1 20 12zM8 9c0-.5.4-1 1-1h.5c.3 0 .5.2.6.4l.7 1.7c.1.2 0 .5-.1.7l-.6.6a6 6 0 0 0 2.7 2.7l.6-.6c.2-.1.5-.2.7-.1l1.7.7c.2.1.4.3.4.6V15a1 1 0 0 1-1 1 7 7 0 0 1-7-7z"),
  google: (p: IconProps) => (<Icon {...p}><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></Icon>),
  send: path("M22 2L11 13M22 2l-7 20-4-9-9-4z"),
  alert: (p: IconProps) => (<Icon {...p}><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></Icon>),
  logout: path("M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"),
  sparkle: path("M12 3l1.7 4.8L18.5 9.5l-4.8 1.7L12 16l-1.7-4.8L5.5 9.5l4.8-1.7z"),
  sun: (p: IconProps) => (<Icon {...p}><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/></Icon>),
  moon: path("M21 12.8A9 9 0 0 1 11.2 3a7 7 0 1 0 9.8 9.8z"),
} as const;

export type IconName = keyof typeof Icons;
