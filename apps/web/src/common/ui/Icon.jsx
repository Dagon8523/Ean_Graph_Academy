import { ICON_SPRITE } from './iconSprite.js';

// Sprite estático y confiable (definido en el código), se inserta una sola vez.
export function IconSprite() {
  return <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true"><defs dangerouslySetInnerHTML={{ __html: ICON_SPRITE }} /></svg>;
}

export function Icon({ name, size = 'md', className = '', style }) {
  return (
    <svg className={`ico ${size === 'sm' ? 'ico-sm' : ''} ${className}`} style={style} aria-hidden="true" focusable="false">
      <use href={`#i-${name}`} />
    </svg>
  );
}
