import{r as React,s as supabase,j as jsx}from"./index-BpXf34zV.js";import{M as MapPin,C as NewAirMap}from"./NewAirMap-CWkQZjU2.js";
const DEFAULT_POINTS=[
  {id:"spawn",title:"Spawn NewAir",description:"Point d'arrivée principal de la ville.",x:50,y:58,color:"#5f96d6",image_url:null},
  {id:"lspd",title:"LSPD",description:"Commissariat et zone d'intervention des forces de l'ordre.",x:47,y:45,color:"#3b82f6",image_url:null},
  {id:"hopital",title:"Hôpital",description:"Urgences, soins et services médicaux.",x:54,y:43,color:"#ef4444",image_url:null},
  {id:"mecano",title:"Garage mécanique",description:"Réparations, customisations et dépannages.",x:42,y:61,color:"#f59e0b",image_url:null},
  {id:"nord",title:"Blaine County",description:"Zone nord, routes, farms et scènes RP extérieures.",x:55,y:27,color:"#22c55e",image_url:null}
];
function cleanPoints(data){
  if(!Array.isArray(data)||data.length===0)return DEFAULT_POINTS;
  return data.map((p,i)=>({
    id:p.id??`point_${i}`,
    title:p.title||p.name||"Lieu NewAir",
    description:p.description||"Lieu référencé sur la carte NewAir.",
    x:Number.isFinite(Number(p.x))?Number(p.x):50,
    y:Number.isFinite(Number(p.y))?Number(p.y):50,
    color:p.color||"#5f96d6",
    image_url:p.image_url||null
  }));
}
function h(){
  const[points,setPoints]=React.useState(DEFAULT_POINTS);
  const[status,setStatus]=React.useState("Chargement des lieux...");
  React.useEffect(()=>{
    let alive=true;
    const load=async()=>{
      try{
        const{data,error}=await supabase.from("map_points").select("*").order("created_at",{ascending:true});
        if(!alive)return;
        if(error)throw error;
        const next=cleanPoints(data);
        setPoints(next);
        setStatus(next===DEFAULT_POINTS?"Carte par défaut chargée":"Carte chargée");
      }catch(err){
        if(alive){setPoints(DEFAULT_POINTS);setStatus("Carte par défaut chargée");}
      }
    };
    load();
    let channel=null;
    try{
      channel=supabase.channel("map_points-public").on("postgres_changes",{event:"*",schema:"public",table:"map_points"},load).subscribe();
    }catch{}
    return()=>{alive=false;if(channel)try{supabase.removeChannel(channel)}catch{}};
  },[]);
  return jsx.jsx(jsx.Fragment,{children:jsx.jsx("main",{className:"pt-28 pb-20 px-6 lg:px-10 bg-transparent min-h-screen",children:jsx.jsxs("div",{className:"max-w-7xl mx-auto",children:[
    jsx.jsxs("div",{className:"text-center mb-10",children:[
      jsx.jsx("p",{className:"text-xs tracking-[0.4em] text-amber-400/80 mb-3",children:"VUE SATELLITE"}),
      jsx.jsx("h1",{className:"text-4xl md:text-6xl font-black tracking-tight text-white",children:"MAP NewAir"}),
      jsx.jsx("p",{className:"text-white/60 mt-4 max-w-2xl mx-auto text-sm md:text-base",children:"Explorez la ville. Survolez les points pour découvrir les lieux marquants de NewAir."}),
      jsx.jsxs("div",{className:"mt-4 inline-flex items-center gap-2 text-xs text-white/50",children:[jsx.jsx(MapPin,{className:"w-3.5 h-3.5"})," ",points.length," lieu",points.length>1?"x":""," référencé",points.length>1?"s":""," • ",status]})
    ]}),
    jsx.jsx("div",{className:"h-[80vh] max-h-[1000px] w-full",children:jsx.jsx(NewAirMap,{points})})
  ]})})})}
export{h as component};
