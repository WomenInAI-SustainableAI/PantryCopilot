import * as React from "react";

const Logo = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 256 256"
    width={32}
    height={32}
    {...props}
  >
    <path fill="none" d="M0 0h256v256H0z" />
    <path
      d="M128 24a104 104 0 0 0-16.3 203.8c1.1-2.3 2.5-4.6 2.5-7.2 0-19.8-12-36.9-12-36.9s32-49.3 32-85.7c0-43.1-40.2-49-40.2-49s-1.8 28.5 12.2 49c-2.3 1.2-12.2 6.1-12.2 14.8 0 8.6 15.1 12.8 15.1 12.8s-31.9 8.2-31.9 39.5c0 23.3 11.5 35.2 13.5 37.3A104 104 0 1 0 128 24Z"
      fill="currentColor"
    />
  </svg>
);

export default Logo;
