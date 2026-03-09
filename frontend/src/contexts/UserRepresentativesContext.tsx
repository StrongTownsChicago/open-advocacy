import React, { useState, useEffect, createContext, useContext } from 'react';
import { Entity } from '../types';
import { representativeStorage } from '../utils/localStorage';

interface UserRepresentativesContextType {
  userRepresentatives: Entity[];
  userAddress: string;
  userDistricts: string[];
  updateUserRepresentatives: (reps: Entity[], address: string, districts: string[]) => void;
  hasUserRepresentatives: boolean;
  clearUserRepresentatives: () => void;
}

const UserRepresentativesContext = createContext<UserRepresentativesContextType>({
  userRepresentatives: [],
  userAddress: '',
  userDistricts: [],
  updateUserRepresentatives: () => {},
  hasUserRepresentatives: false,
  clearUserRepresentatives: () => {},
});

interface UserRepresentativesProviderProps {
  children: React.ReactNode;
}

export const UserRepresentativesProvider: React.FC<UserRepresentativesProviderProps> = ({
  children,
}) => {
  const [userRepresentatives, setUserRepresentatives] = useState<Entity[]>([]);
  const [userAddress, setUserAddress] = useState<string>('');
  const [userDistricts, setUserDistricts] = useState<string[]>([]);

  // Load data from localStorage on mount
  useEffect(() => {
    const storedData = representativeStorage.loadRepresentativeData();
    setUserRepresentatives(storedData.representatives);
    setUserAddress(storedData.address);
    setUserDistricts(storedData.districts);
  }, []);

  // Update user representatives and store in localStorage
  const updateUserRepresentatives = (reps: Entity[], address: string, districts: string[]) => {
    setUserRepresentatives(reps);
    setUserAddress(address);
    setUserDistricts(districts);

    representativeStorage.saveRepresentativeData({
      representatives: reps,
      address,
      districts,
    });
  };

  const clearUserRepresentatives = () => {
    setUserRepresentatives([]);
    setUserAddress('');
    setUserDistricts([]);
    representativeStorage.clearRepresentativeData();
  };

  return (
    <UserRepresentativesContext.Provider
      value={{
        userRepresentatives,
        userAddress,
        userDistricts,
        updateUserRepresentatives,
        hasUserRepresentatives: userRepresentatives.length > 0,
        clearUserRepresentatives,
      }}
    >
      {children}
    </UserRepresentativesContext.Provider>
  );
};

// Custom hook for accessing the context
// eslint-disable-next-line react-refresh/only-export-components
export const useUserRepresentatives = () => {
  const context = useContext(UserRepresentativesContext);
  if (context === undefined) {
    throw new Error('useUserRepresentatives must be used within a UserRepresentativesProvider');
  }
  return context;
};
