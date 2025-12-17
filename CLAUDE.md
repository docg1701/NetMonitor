# CLAUDE.md - Notas para o Agente de Desenvolvimento

## Ionic Angular - IMPORTANTE

### Nunca misturar Standalone e Modules

O Ionic Angular possui duas abordagens de build que **NÃO PODEM ser usadas ao mesmo tempo**:

1. **Modules** - usa `IonicModule.forRoot()` e imports de `@ionic/angular`
2. **Standalone** - usa imports individuais de `@ionic/angular/standalone`

**Regra:** Se o projeto usa `IonicModule.forRoot()` no `app.module.ts`, todos os componentes devem importar `IonicModule` de `@ionic/angular`, e **NUNCA** de `@ionic/angular/standalone`.

**Exemplo ERRADO (causa quebra do CSS no dev server):**
```typescript
// app.module.ts usa IonicModule.forRoot()
// MAS app.component.ts importa de standalone:
import { IonApp, IonRouterOutlet } from '@ionic/angular/standalone'; // ERRADO!
```

**Exemplo CORRETO:**
```typescript
// app.module.ts usa IonicModule.forRoot()
// app.component.ts também usa IonicModule:
import { IonicModule } from '@ionic/angular'; // CORRETO!
```

**Sintoma do problema:** O app funciona quando compilado para produção (AppImage), mas no dev server (`npm run tauri dev`) o CSS/design fica completamente quebrado, mostrando apenas dados crus sem estilização.

**Fonte:** https://ionicframework.com/docs/angular/build-options

## Tauri + Mold Linker

O projeto usa `mold` como linker para acelerar compilações Rust. Configuração em `.cargo/config.toml`:

```toml
[build]
jobs = 28

[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "link-arg=-fuse-ld=mold"]
```

**Nota:** Após `cargo clean`, a primeira compilação demora ~2-5 minutos pois recompila todas as dependências. Compilações subsequentes são rápidas (~10-40 segundos).

## Tauri + Ícones PNG (Linux)

**Problema:** Ícones PNG com 16-bit de profundidade causam corrupção visual no ícone da janela (taskbar) no Linux. O ícone do arquivo AppImage aparece correto, mas o ícone da janela mostra pixels aleatórios.

**Causa:** GTK/GDK e o Tauri esperam ícones 8-bit RGBA (32-bit total). Ícones 16-bit por canal (64-bit total) não são renderizados corretamente.

**Solução:** Converter todos os ícones para 8-bit RGBA:
```bash
cd netmonitor/src-tauri/icons
for f in *.png; do convert "$f" -depth 8 PNG32:"$f"; done
```

**Verificação:**
```bash
identify -verbose icon.png | grep "Type:"
# Deve mostrar: Type: TrueColorAlpha
```

## Estrutura do Projeto

- `netmonitor/` - Código Angular/Ionic
- `netmonitor/src-tauri/` - Código Rust/Tauri
- `docs/` - Documentação e stories

## Bug Crítico: Hot Reload Quebrado (Angular 21 + Vite + Ionic 8)

**Problema:** O servidor de desenvolvimento (`ng serve` / `ionic serve`) quebra após a primeira alteração de arquivo (Hot Module Replacement - HMR) com o erro:
`InvalidCharacterError: Invalid qualified name start in '[object Object]'`

**Causa:** Incompatibilidade entre o processo de hidratação do Ionic 8 e o build system do Angular 21 com Vite.

**Recomendação de Fluxo de Trabalho (Workaround Definitivo):**
1. **NÃO use `ng serve` ou `ionic serve`**. O HMR está quebrado.
2. **Use `npm run test:visual`**: Este comando customizado faz o build completo (Angular + Rust/Tauri) e executa a aplicação nativa.
   - É rápido (graças ao linker `mold` e `esbuild`).
   - É confiável (testa o binário real).
   - Comando: `npm run test:visual` (na pasta `netmonitor`)
3. **Testes de Lógica:** Continue usando `npm test` para feedback imediato de lógica.