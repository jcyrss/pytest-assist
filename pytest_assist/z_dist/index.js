let root

const hash_router = {
  ''     : '/func1.js',
  // 'func1' : '/func1.js',
  // 'charger'     : {fileName: '/device.js', className:'Charger'},
}

let hashEntries = Object.entries(hash_router)

const ModuleFile2Element = {} 

async function routerChanged(){
  let url = window.location.hash.slice(1)

  let componentDesc = null 

  console.log('route url is', url)

  for (let [key, value] of hashEntries) {
    if (url.startsWith(key)){
      componentDesc = value
      break
    }    
  }

  if (!componentDesc){
    alert('functionality not implemented!')
    return
  }

  
  let element = ModuleFile2Element[url]

  if (!element) {    
    if(typeof componentDesc === 'string'){
      // let { default: DClass }  = await import(componentDesc);
      // Component = DClass
      Component  = (await import(componentDesc)).default;
    }
    else{
      Component  = (await import(componentDesc.fileName))[componentDesc.className]
    }

    element = React.createElement(Component)
    
    ModuleFile2Element[url] = element
  }  

  root.render(element);

}

window.onload = function(){
  
  window.addEventListener('hashchange', function() {
    routerChanged()
  });
  
  root = ReactDOM.createRoot(document.querySelector('main'));
  
  routerChanged();

}