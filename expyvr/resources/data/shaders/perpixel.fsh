varying vec3 N;
varying vec3 v;
uniform sampler2D tex;

struct gl_LightSourceParameters {
 vec4 ambient;              // Acli
 vec4 diffuse;              // Dcli
 vec4 specular;             // Scli
 vec4 position;             // Ppli
 vec4 halfVector;           // Derived: Hi
 vec3 spotDirection;        // Sdli
 float spotExponent;        // Srli
 float spotCutoff;          // Crli
                            // (range: [0.0,90.0], 180.0)
 float spotCosCutoff;       // Derived: cos(Crli)
                            // (range: [1.0,0.0],-1.0)
 float constantAttenuation; // K0
 float linearAttenuation;   // K1
 float quadraticAttenuation;// K2
};

uniform gl_LightSourceParameters gl_LightSource[gl_MaxLights];

struct gl_MaterialParameters
{
 vec4 emission;    // Ecm
 vec4 ambient;     // Acm
 vec4 diffuse;     // Dcm
 vec4 specular;    // Scm
 float shininess;  // Srm
};
uniform gl_MaterialParameters gl_FrontMaterial;
uniform gl_MaterialParameters gl_BackMaterial;

struct gl_LightModelProducts
{
  vec4 sceneColor; // Derived. Ecm + Acm * Acs
};
uniform gl_LightModelProducts gl_FrontLightModelProduct;
uniform gl_LightModelProducts gl_BackLightModelProduct;


struct gl_LightProducts {
 vec4 ambient;    // Acm * Acli 
 vec4 diffuse;    // Dcm * Dcli
 vec4 specular;   // Scm * Scli
};
uniform gl_LightProducts gl_FrontLightProduct[gl_MaxLights];
uniform gl_LightProducts gl_BackLightProduct[gl_MaxLights];

void main (void)
{
    vec3 L0 = normalize(gl_LightSource[0].position.xyz - v); 
    vec3 L1 = normalize(gl_LightSource[1].position.xyz - v); 
    vec3 E = normalize(-v); // we are in Eye Coordinates, so EyePos is (0,0,0)
    vec3 R0 = normalize(-reflect(L0,N)); 
    vec3 R1 = normalize(-reflect(L1,N)); 

    //calculate Ambient Term:
    vec4 Iamb = gl_FrontLightProduct[0].ambient + gl_FrontLightProduct[1].ambient;

    //calculate Diffuse Term:
    vec4 Idiff = gl_FrontLightProduct[0].diffuse * max(dot(N,L0), 0.0) + 
                 gl_FrontLightProduct[1].diffuse * max(dot(N,L1), 0.0);

    // calculate Specular Term:
    vec4 Ispec = gl_FrontLightProduct[0].specular * pow(max(dot(R0,E),0.0),0.3*gl_FrontMaterial.shininess) +
                 gl_FrontLightProduct[1].specular * pow(max(dot(R1,E),0.0),0.3*gl_FrontMaterial.shininess);


    // write Total Color:
    gl_FragColor = gl_FrontLightModelProduct.sceneColor + Iamb + Idiff + Ispec; 
}