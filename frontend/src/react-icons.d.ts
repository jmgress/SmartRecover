declare module 'react-icons/fi' {
  import { ComponentType, SVGAttributes } from 'react';
  
  interface IconBaseProps extends SVGAttributes<SVGElement> {
    size?: string | number;
  }
  
  export const FiSettings: ComponentType<IconBaseProps>;
  export const FiUser: ComponentType<IconBaseProps>;
}
