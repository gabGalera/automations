const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const mustache = require('mustache');

const projectRoot = path.join(__dirname, '..');
const projectName = 'AutomacoesPainel';
const namespace = 'AutomacoesPainel';
const rnwPath = path.dirname(
  require.resolve('react-native-windows/package.json', {paths: [projectRoot]}),
);
const rnwVersion = require(path.join(rnwPath, 'package.json')).version;
const projectGuid = crypto.randomUUID();
const packageGuid = crypto.randomUUID();
const mainComponentName = require(path.join(projectRoot, 'app.json')).name;

const replacements = {
  useMustache: true,
  regExpPatternsToRemove: [],
  name: projectName,
  namespace,
  namespaceCpp: namespace,
  rnwVersion,
  rnwPathFromProjectRoot: path
    .relative(projectRoot, rnwPath)
    .replace(/\//g, '\\'),
  mainComponentName,
  projectGuidLower: `{${projectGuid.toLowerCase()}}`,
  projectGuidUpper: `{${projectGuid.toUpperCase()}}`,
  packageGuidLower: `{${packageGuid.toLowerCase()}}`,
  packageGuidUpper: `{${packageGuid.toUpperCase()}}`,
  currentUser: process.env.USERNAME || 'user',
  devMode: false,
  useNuGets: true,
  addReactNativePublicAdoFeed: true,
  cppNugetPackages: [],
  autolinkPropertiesForProps: '',
  autolinkProjectReferencesForTargets: '',
  autolinkCppIncludes: '',
  autolinkCppPackageProviders:
    '\n    UNREFERENCED_PARAMETER(packageProviders);',
};

function resolveContents(srcPath) {
  let content = fs.readFileSync(srcPath, 'utf8');
  return mustache.render(content, replacements);
}

function copyTemplateFile(from, to) {
  const target = path.join(projectRoot, to.replace(/MyApp/g, projectName));
  fs.mkdirSync(path.dirname(target), {recursive: true});
  const extension = path.extname(from);
  if (['.png', '.jar', '.keystore', '.ico', '.rc'].includes(extension)) {
    fs.copyFileSync(from, target);
    return;
  }
  fs.writeFileSync(target, resolveContents(from), 'utf8');
}

function listFiles(dir, base = dir) {
  const entries = fs.readdirSync(dir, {withFileTypes: true});
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFiles(full, base));
    } else {
      files.push(path.relative(base, full));
    }
  }
  return files;
}

const templateRoot = path.join(rnwPath, 'templates', 'cpp-app');
const files = listFiles(templateRoot).filter(
  file => file !== 'template.config.js',
);

for (const file of files) {
  let target = file;
  if (path.basename(file) === '_gitignore') {
    target = path.join(path.dirname(file), '.gitignore');
  }
  if (path.basename(file) === 'NuGet_Config') {
    target = path.join(path.dirname(file), 'NuGet.config');
  }
  copyTemplateFile(path.join(templateRoot, file), target);
  console.log(`wrote ${target.replace(/MyApp/g, projectName)}`);
}

const pkgPath = path.join(projectRoot, 'package.json');
const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
pkg.scripts = {
  ...pkg.scripts,
  windows: 'npx @react-native-community/cli run-windows',
  'test:windows': 'jest --config jest.config.windows.js',
};
pkg.devDependencies = {
  ...pkg.devDependencies,
  '@rnx-kit/jest-preset': '^0.3.1',
};
fs.writeFileSync(pkgPath, `${JSON.stringify(pkg, null, 2)}\n`, 'utf8');
console.log('Windows project bootstrapped.');
