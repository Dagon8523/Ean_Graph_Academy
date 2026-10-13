import { useTheme } from '../../core/theme.jsx';
export function Logo({ className = 'logo', title = 'Universidad EAN' }) {
 const { theme } = useTheme();
 return <img className={className} src={`/brand/logo-ean-universidad-${theme === 'dark' ? 'negativo' : 'positivo'}.svg`} alt={title} />;
}
export function BrandSymbol({ className, decorative = true }) {
  return (
    <img
      className={className}
      src={className === 'pattern'
        ? '/brand/simbolo-ean-verde.svg'
        : '/brand/simbolo-ean.svg'}
      alt={decorative ? '' : 'Símbolo Universidad EAN'}
      aria-hidden={decorative || undefined}
    />
  );
}
export function Vigilada() { return <span className="vigilada" aria-label="Vigilada Mineducación"><span className="l">Vigilada </span><span className="b">Min</span><span className="l">educación</span></span>; }
