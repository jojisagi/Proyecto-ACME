import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute
} from 'amazon-cognito-identity-js';

// Configuración de Cognito
const poolData = {
  UserPoolId: process.env.REACT_APP_USER_POOL_ID || 'YOUR_USER_POOL_ID',
  ClientId: process.env.REACT_APP_CLIENT_ID || 'YOUR_CLIENT_ID'
};

const userPool = new CognitoUserPool(poolData);

// Registrar nuevo usuario
export const signUp = (email, password) => {
  return new Promise((resolve, reject) => {
    const attributeList = [
      new CognitoUserAttribute({
        Name: 'email',
        Value: email
      })
    ];

    userPool.signUp(email, password, attributeList, null, (err, result) => {
      if (err) {
        reject(err);
        return;
      }
      resolve(result.user);
    });
  });
};

// Iniciar sesión
export const signIn = (email, password) => {
  return new Promise((resolve, reject) => {
    const authenticationDetails = new AuthenticationDetails({
      Username: email,
      Password: password
    });

    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool
    });

    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (result) => {
        const idToken = result.getIdToken().getJwtToken();
        const accessToken = result.getAccessToken().getJwtToken();
        
        resolve({
          email: email,
          idToken: idToken,
          accessToken: accessToken
        });
      },
      onFailure: (err) => {
        reject(err);
      }
    });
  });
};

// Cerrar sesión
export const signOut = () => {
  const cognitoUser = userPool.getCurrentUser();
  if (cognitoUser) {
    cognitoUser.signOut();
  }
};

// Obtener usuario actual
export const getCurrentUser = () => {
  return new Promise((resolve, reject) => {
    const cognitoUser = userPool.getCurrentUser();

    if (!cognitoUser) {
      reject(new Error('No hay usuario autenticado'));
      return;
    }

    cognitoUser.getSession((err, session) => {
      if (err) {
        reject(err);
        return;
      }

      if (!session.isValid()) {
        reject(new Error('Sesión inválida'));
        return;
      }

      cognitoUser.getUserAttributes((err, attributes) => {
        if (err) {
          reject(err);
          return;
        }

        const email = attributes.find(attr => attr.Name === 'email')?.Value;
        const idToken = session.getIdToken().getJwtToken();
        const accessToken = session.getAccessToken().getJwtToken();

        resolve({
          email: email,
          idToken: idToken,
          accessToken: accessToken
        });
      });
    });
  });
};
